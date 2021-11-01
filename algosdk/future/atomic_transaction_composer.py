import copy
from enum import IntEnum
import json

from algosdk import error
from algosdk.abi import method
from algosdk.future import transaction


class AtomicTransactionComposerStatus(IntEnum):
    # BUILDING indicates that the atomic group is still under construction
    BUILDING = 0

    # BUILT indicates that the atomic group has been finalized,
    # but not yet signed.
    BUILT = 1

    # SIGNED indicates that the atomic group has been finalized and signed,
    # but not yet submitted to the network.
    SIGNED = 2

    # SUBMITTED indicates that the atomic group has been finalized, signed,
    # and submitted to the network.
    SUBMITTED = 3

    # COMMITTED indicates that the atomic group has been finalized, signed,
    # submitted, and successfully committed to a block.
    COMMITTED = 4


class AtomicTransactionComposer:
    """
    Constructs an atomic transaction group which may contain a combination of
    Transactions and ABI Method calls.

    Args:
        status (AtomicTransactionComposerStatus): IntEnum representing the current state of the composer
        txn_count (int): number of transactions in the group
        txn_list (list[TransactionWithSigner]): list of transactions with signers
        signed_txns (list[SignedTransaction]): list of signed transactions
        tx_ids (list[str]): list of individual transaction IDs in this atomic group
        atomic_tx_id (str): transaction ID of this atomic group
    """

    MAX_GROUP_SIZE = 16

    def __init__(self) -> None:
        self.status = AtomicTransactionComposerStatus.BUILDING
        self.txn_count = 0
        self.method_list = []
        self.txn_list = []
        self.signed_txns = []
        self.tx_ids = []
        self.atomic_tx_id = None

    def get_status(self):
        """
        Returns the status of this composer's transaction group.
        """
        return self.status

    def get_tx_count(self):
        """
        Returns the number of transactions currently in this atomic group.
        """
        return self.txn_count

    def clone(self):
        """
        Creates a new composer with the same underlying transactions.
        The new composer's status will be BUILDING, so additional transactions
        may be added to it.
        """
        cloned = copy.deepcopy(self)
        cloned.status = AtomicTransactionComposerStatus.BUILDING
        return cloned

    def add_transaction(self, txn_and_signer):
        """
        Adds a transaction to this atomic group.

        An error will be thrown if the composer's status is not BUILDING,
        or if adding this transaction causes the current group to exceed
        MAX_GROUP_SIZE.

        Args:
            txn_and_signer (TransactionWithSigner)
        """
        if not self.status == AtomicTransactionComposerStatus.BUILDING:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer must be in BUILDING state for a transaction to be added"
            )
        if self.txn_count == self.MAX_GROUP_SIZE:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer cannot exceed MAX_GROUP_SIZE transactions"
            )
        self.txn_list.append(txn_and_signer)
        self.txn_count += 1

    def add_method_call(
        self,
        app_id,
        method_call,
        sender,
        sp,
        signer,
        method_args=None,
        on_complete=transaction.OnComplete.NoOpOC,
        note=None,
        lease=None,
        rekey_to=None,
    ):
        """
        Add a smart contract method call to this atomic group.

        An error will be thrown if the composer's status is not BUILDING,
        if adding this transaction causes the current group to exceed
        MAX_GROUP_SIZE, or if the provided arguments are invalid for
        the given method.

        Args:
            app_id (int): application id of app that the method is being invoked on
            method_call (Method): ABI method object with initialized arguments and return types
            sender (str): address of the sender
            sp (SuggestedParams): suggested params from algod
            signer (TransactionSigner): signer that will sign the transactions
            method_args (list[ABIValue | TransactionWithSigner], optional): list of arguments to be encoded
                or transactions that immediate precede this method call
            on_complete (OnComplete, optional): intEnum representing what app should do on completion
                and if blank, it will default to a NoOp call
            note (bytes, optional): arbitrary optional bytes
            lease (byte[32], optional): specifies a lease, and no other transaction
                with the same sender and lease can be confirmed in this
                transaction's valid rounds
            rekey_to (str, optional): additionally rekey the sender to this address

        """
        if not self.status == AtomicTransactionComposerStatus.BUILDING:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer must be in BUILDING state for a transaction to be added"
            )
        if self.txn_count + method_call.get_txn_calls() > self.MAX_GROUP_SIZE:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer cannot exceed MAX_GROUP_SIZE transactions"
            )
        if len(method_call.args) != len(method_args):
            raise error.AtomicTransactionComposerError(
                "number of method arguments do not match the method signature"
            )
        if not isinstance(method_call, method.Method):
            raise error.AtomicTransactionComposerError(
                "invalid Method object was passed into AtomicTransactionComposer"
            )

        app_args = []
        # First app arg must be the selector of the method
        app_args.append(method_call.get_selector())
        # Iterate through the method arguments and either pack a transaction
        # or encode a ABI value.
        for i, arg in enumerate(method_call.args):
            if arg in method.TRANSACTION_ARGS:
                if not (method_args[i], TransactionWithSigner):
                    raise error.AtomicTransactionComposerError(
                        "expected TransactionWithSigner as method argument, but received: {}".format(
                            method_args[i]
                        )
                    )
                self.txn_list.append(method_args[i])
            else:
                encoded_arg = arg.encode(method_args[i])
                app_args.append(encoded_arg)
        self.txn_count += method_call.get_txn_calls()
        self.method_list.append(method_call)

        # Create a method call transaction
        method_txn = transaction.ApplicationCallTxn(
            sender=sender,
            sp=sp,
            index=app_id,
            on_complete=on_complete,
            app_args=app_args,
            note=note,
            lease=lease,
            rekey_to=rekey_to,
        )
        txn_with_signer = TransactionWithSigner(method_txn, signer)
        self.txn_list.append(txn_with_signer)

    def build_group(self):
        """
        Finalize the transaction group and returns the finalized transactions with signers.
        The composer's status will be at least BUILT after executing this method.

        Returns:
            list[TransactionWithSigner]: list of transactions with signers
        """
        if self.status < AtomicTransactionComposerStatus.BUILT:
            self.status = AtomicTransactionComposerStatus.BUILT

        # Get group transaction id
        group_txns = [t.txn for t in self.txn_list]
        group_id = transaction.calculate_group_id(group_txns)
        for t in self.txn_list:
            t.txn.group = group_id
            self.tx_ids.append(t.txn.get_txid())

        return self.txn_list

    def gather_signatures(self):
        """
        Obtain signatures for each transaction in this group. If signatures have already been obtained,
        this method will return cached versions of the signatures.
        The composer's status will be at least SIGNED after executing this method.
        An error will be thrown if signing any of the transactions fails.

        Returns:
            list[SignedTransactions]: list of signed transactions
        """
        if self.status < AtomicTransactionComposerStatus.SIGNED:
            self.build_group()
            self.status = AtomicTransactionComposerStatus.SIGNED
        if self.signed_txns:
            # Return cached versions of the signatures
            return self.signed_txns

        for txn_with_signer in self.txn_list:
            unsigned_txn = txn_with_signer.txn
            stxn = txn_with_signer.signer.sign_txn(unsigned_txn)
            self.signed_txns.append(stxn)
        return self.signed_txns

    def submit(self, client):
        """
        Send the transaction group to the network, but don't wait for it to be
        committed to a block. An error will be thrown if submission fails.
        The composer's status must be SUBMITTED or lower before calling this method.
        If submission is successful, this composer's status will update to SUBMITTED.

        Note: a group can only be submitted again if it fails.

        Returns:
            list[Transaction]: list of submitted transactions
        """
        if self.status <= AtomicTransactionComposerStatus.SUBMITTED:
            self.build_group()
            self.gather_signatures()
            self.status = AtomicTransactionComposerStatus.SUBMITTED
        else:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposerStatus must be submitted or lower to submit a group"
            )

        self.atomic_tx_id = client.send_transactions(self.signed_txns)

        return self.tx_ids

    def execute(self, client):
        """
        Send the transaction group to the network and wait until it's committed
        to a block. An error will be thrown if submission or execution fails.
        The composer's status must be SUBMITTED or lower before calling this method,
        since execution is only allowed once. If submission is successful,
        this composer's status will update to SUBMITTED.
        If the execution is also successful, this composer's status will update to COMMITTED.

        Note: a group can only be submitted again if it fails.

        Returns:
            AtomicTransactionResponse: Object with confirmed round for this transaction,
                a list of txIDs of the submitted transactions, and an array of
                results for each method call transaction in this group. If a
                method has no return value (void), then the method results array
                will contain None for that method's return value.
        """
        if self.status <= AtomicTransactionComposerStatus.SUBMITTED:
            self.build_group()
            self.gather_signatures()
            self.status = AtomicTransactionComposerStatus.COMMITTED
        else:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposerStatus must be submitted or lower to execute a group"
            )

        client.wait_for_confirmation(client, self.atomic_tx_id)

        resp = client.pending_transaction_info(self.atomic_tx_id)
        resp_dict = json.loads(resp)

        confirmed_round = resp_dict["confirmed-round"]
        tx_ids = self.tx_ids
        results = resp_dict["logs"] if "logs" in resp_dict else None

        method_results = []
        for i, result in enumerate(results):
            if self.method_list[i].Returns.type == "void":
                method_results.append(None)
            else:
                return_value = self.method_list[i].Returns.type.decode(result)
                method_results.append(return_value)

        return AtomicTransactionResponse(
            confirmed_round=confirmed_round,
            tx_ids=tx_ids,
            results=method_results,
        )


class TransactionSigner:
    """
    Represents a function which can sign transactions from an atomic transaction group.

    Args:
        private_key (str): private key of signing account
        msig (MultiSig, optional): multisig account information
    """

    def __init__(self, private_key, msig=None) -> None:
        self.private_key = private_key
        self.msig = msig

    def sign(self, txn_group, indexes):
        signed_txn = []
        for i in indexes:
            txn = txn_group[i]
            assert isinstance(txn, transaction.Transaction)
            signed_txn.append(self.sign_txn(txn))
        return signed_txn

    def sign_txn(self, txn):
        if self.msig:
            for sk in self.private_key:
                txn.sign(sk)
            return txn
        return txn.sign(self.private_key)


class TransactionWithSigner:
    def __init__(self, txn, signer) -> None:
        self.txn = txn
        self.signer = signer


class AtomicTransactionResponse:
    def __init__(self, confirmed_round, tx_ids=None, results=None) -> None:
        self.confirmed_round = confirmed_round
        self.tx_ids = tx_ids
        self.method_results = results


def make_account_transaction_signer(private_key):
    """
    Creates a TransactionSigner for a basic account or LogicSigAccount
    """
    return TransactionSigner(private_key)


def make_multisig_account_transaction_signer(msig, sks):
    """
    Creates a TransactionSigner for a MultiSig account
    """
    return TransactionSigner(private_key=sks, msig=msig)
