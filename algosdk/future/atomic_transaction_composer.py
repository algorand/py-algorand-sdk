import copy
from enum import IntEnum

from algosdk.future import transaction
from algosdk import error
from algosdk.abi import method


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
    """

    MAX_GROUP_SIZE = 16

    def __init__(self) -> None:
        self.status = AtomicTransactionComposerStatus.BUILDING
        self.txn_count = 0
        self.txn_list = []

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
        return self.txn_list

    def gather_signatures(self):
        pass

    def submit(self, client):
        pass

    def execute(self, client):
        pass


class TransactionSigner:
    def __init__(self, private_key) -> None:
        self.pk = private_key

    def sign(self, txn_group, indexes):
        signed_txn = []
        for i in indexes:
            txn = txn_group[i]
            assert isinstance(txn, transaction.Transaction)
            signed_txn.append(txn.sign(self.pk))
        return signed_txn


class TransactionWithSigner:
    def __init__(self, txn, signer) -> None:
        self.txn = txn
        self.signer = signer


def make_basic_account_transaction_signer(private_key):
    pass


def make_logicsig_account_transaction_signer(private_key):
    pass


def make_multisig_account_transaction_signer(msig, sks):
    pass
