from abc import ABC, abstractmethod
import base64
import copy
from enum import IntEnum
from typing import Any, List, Union

from algosdk import abi, error
from algosdk.abi.base_type import ABIType
from algosdk.future import transaction
from algosdk.v2client import algod

# The first four bytes of an ABI method call return must have this hash
ABI_RETURN_HASH = b"\x15\x1f\x7c\x75"


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
        method_dict (dict): dictionary of an index in the transaction list to a Method object
        txn_list (list[TransactionWithSigner]): list of transactions with signers
        signed_txns (list[SignedTransaction]): list of signed transactions
        tx_ids (list[str]): list of individual transaction IDs in this atomic group
    """

    # The maximum size of an atomic transaction group.
    MAX_GROUP_SIZE = 16
    # The maximum number of app-args that can be individually packed for ABIs
    MAX_ABI_APP_ARG_LIMIT = 14

    def __init__(self) -> None:
        self.status = AtomicTransactionComposerStatus.BUILDING
        self.method_dict = {}
        self.txn_list = []
        self.signed_txns = []
        self.tx_ids = []

    def get_status(self) -> AtomicTransactionComposerStatus:
        """
        Returns the status of this composer's transaction group.
        """
        return self.status

    def get_tx_count(self) -> int:
        """
        Returns the number of transactions currently in this atomic group.
        """
        return len(self.txn_list)

    def clone(self) -> "AtomicTransactionComposer":
        """
        Creates a new composer with the same underlying transactions.
        The new composer's status will be BUILDING, so additional transactions
        may be added to it.
        """
        cloned = AtomicTransactionComposer()
        cloned.method_dict = copy.deepcopy(self.method_dict)
        cloned.txn_list = copy.deepcopy(self.txn_list)
        for t in cloned.txn_list:
            t.txn.group = None
        cloned.status = AtomicTransactionComposerStatus.BUILDING
        return cloned

    def add_transaction(
        self, txn_and_signer: "TransactionWithSigner"
    ) -> "AtomicTransactionComposer":
        """
        Adds a transaction to this atomic group.

        An error will be thrown if the composer's status is not BUILDING,
        or if adding this transaction causes the current group to exceed
        MAX_GROUP_SIZE.

        Args:
            txn_and_signer (TransactionWithSigner)
        """
        if self.status != AtomicTransactionComposerStatus.BUILDING:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer must be in BUILDING state for a transaction to be added"
            )
        if len(self.txn_list) == self.MAX_GROUP_SIZE:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer cannot exceed MAX_GROUP_SIZE {} transactions".format(
                    self.MAX_GROUP_SIZE
                )
            )
        if not isinstance(txn_and_signer, TransactionWithSigner):
            raise error.AtomicTransactionComposerError(
                "expected TransactionWithSigner object to the AtomicTransactionComposer"
            )
        if txn_and_signer.txn.group and txn_and_signer.txn.group != 0:
            raise error.AtomicTransactionComposerError(
                "cannot add a transaction with nonzero group ID"
            )
        self.txn_list.append(txn_and_signer)
        return self

    def add_method_call(
        self,
        app_id: int,
        method: abi.method.Method,
        sender: str,
        sp: transaction.SuggestedParams,
        signer: "TransactionSigner",
        method_args: List[Union[Any]] = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        note: bytes = None,
        lease: bytes = None,
        rekey_to: str = None,
    ) -> "AtomicTransactionComposer":
        """
        Add a smart contract method call to this atomic group.

        An error will be thrown if the composer's status is not BUILDING,
        if adding this transaction causes the current group to exceed
        MAX_GROUP_SIZE, or if the provided arguments are invalid for
        the given method.

        Args:
            app_id (int): application id of app that the method is being invoked on
            method (Method): ABI method object with initialized arguments and return types
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
        if self.status != AtomicTransactionComposerStatus.BUILDING:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer must be in BUILDING state for a transaction to be added"
            )
        if len(self.txn_list) + method.get_txn_calls() > self.MAX_GROUP_SIZE:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer cannot exceed MAX_GROUP_SIZE transactions"
            )
        if not method_args:
            method_args = []
        if len(method.args) != len(method_args):
            raise error.AtomicTransactionComposerError(
                "number of method arguments do not match the method signature"
            )
        if not isinstance(method, abi.method.Method):
            raise error.AtomicTransactionComposerError(
                "invalid Method object was passed into AtomicTransactionComposer"
            )
        if app_id == 0:
            raise error.AtomicTransactionComposerError(
                "application create call not supported"
            )

        app_args = []
        # For more than 14 args, including the selector, compact them into a tuple
        additional_args = []
        additional_types = []
        txn_list = []
        # First app arg must be the selector of the method
        app_args.append(method.get_selector())
        # Iterate through the method arguments and either pack a transaction
        # or encode a ABI value.
        for i, arg in enumerate(method.args):
            if arg.type in abi.method.TRANSACTION_ARGS:
                if not isinstance(method_args[i], TransactionWithSigner):
                    raise error.AtomicTransactionComposerError(
                        "expected TransactionWithSigner as method argument, but received: {}".format(
                            method_args[i]
                        )
                    )
                if method_args[i].txn.group and method_args[i].txn.group != 0:
                    raise error.AtomicTransactionComposerError(
                        "cannot add a transaction with nonzero group ID"
                    )
                txn_list.append(method_args[i])
            elif len(app_args) > self.MAX_ABI_APP_ARG_LIMIT:
                # Pack the remaining values as a tuple
                additional_types.append(arg.type)
                additional_args.append(method_args[i])
            else:
                encoded_arg = arg.type.encode(method_args[i])
                app_args.append(encoded_arg)

        if additional_args:
            remainder_args = abi.TupleType(additional_types).encode(
                additional_args
            )
            app_args.append(remainder_args)

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
        txn_list.append(txn_with_signer)

        self.txn_list += txn_list
        self.method_dict[len(self.txn_list) - 1] = method
        return self

    def build_group(self) -> list:
        """
        Finalize the transaction group and returns the finalized transactions with signers.
        The composer's status will be at least BUILT after executing this method.

        Returns:
            list[TransactionWithSigner]: list of transactions with signers
        """
        if self.status >= AtomicTransactionComposerStatus.BUILT:
            return self.txn_list
        if not self.txn_list:
            raise error.AtomicTransactionComposerError(
                "no transactions to build for AtomicTransactionComposer"
            )

        # Get group transaction id
        group_txns = [t.txn for t in self.txn_list]
        group_id = transaction.calculate_group_id(group_txns)
        for t in self.txn_list:
            t.txn.group = group_id
            self.tx_ids.append(t.txn.get_txid())

        self.status = AtomicTransactionComposerStatus.BUILT
        return self.txn_list

    def gather_signatures(self) -> list:
        """
        Obtain signatures for each transaction in this group. If signatures have already been obtained,
        this method will return cached versions of the signatures.
        The composer's status will be at least SIGNED after executing this method.
        An error will be thrown if signing any of the transactions fails.

        Returns:
            list[SignedTransactions]: list of signed transactions
        """
        if self.status >= AtomicTransactionComposerStatus.SIGNED:
            # Return cached versions of the signatures
            return self.signed_txns

        stxn_list = [None] * len(self.txn_list)
        signer_indexes = {}  # Map a signer to a list of indices to sign
        txn_list = self.build_group()
        for i, txn_with_signer in enumerate(txn_list):
            if txn_with_signer.signer not in signer_indexes:
                signer_indexes[txn_with_signer.signer] = []
            signer_indexes[txn_with_signer.signer].append(i)

        # Sign then merge the signed transactions in order
        txns = [t.txn for t in self.txn_list]
        for signer, indexes in signer_indexes.items():
            stxns = signer.sign_transactions(txns, indexes)
            for i, stxn in enumerate(stxns):
                index = indexes[i]
                stxn_list[index] = stxn

        if None in stxn_list:
            raise error.AtomicTransactionComposerError(
                "missing signatures, got {}".format(stxn_list)
            )

        self.status = AtomicTransactionComposerStatus.SIGNED
        self.signed_txns = stxn_list
        return self.signed_txns

    def submit(self, client: algod.AlgodClient) -> list:
        """
        Send the transaction group to the network, but don't wait for it to be
        committed to a block. An error will be thrown if submission fails.
        The composer's status must be SUBMITTED or lower before calling this method.
        If submission is successful, this composer's status will update to SUBMITTED.

        Note: a group can only be submitted again if it fails.

        Args:
            client (AlgodClient): Algod V2 client

        Returns:
            list[Transaction]: list of submitted transactions
        """
        if self.status <= AtomicTransactionComposerStatus.SUBMITTED:
            self.gather_signatures()
        else:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposerStatus must be submitted or lower to submit a group"
            )

        client.send_transactions(self.signed_txns)
        self.status = AtomicTransactionComposerStatus.SUBMITTED
        return self.tx_ids

    def execute(
        self, client: algod.AlgodClient, wait_rounds: int
    ) -> "AtomicTransactionResponse":
        """
        Send the transaction group to the network and wait until it's committed
        to a block. An error will be thrown if submission or execution fails.
        The composer's status must be SUBMITTED or lower before calling this method,
        since execution is only allowed once. If submission is successful,
        this composer's status will update to SUBMITTED.
        If the execution is also successful, this composer's status will update to COMMITTED.

        Note: a group can only be submitted again if it fails.

        Args:
            client (AlgodClient): Algod V2 client
            wait_rounds (int): maximum number of rounds to wait for transaction confirmation

        Returns:
            AtomicTransactionResponse: Object with confirmed round for this transaction,
                a list of txIDs of the submitted transactions, and an array of
                results for each method call transaction in this group. If a
                method has no return value (void), then the method results array
                will contain None for that method's return value.
        """
        if self.status > AtomicTransactionComposerStatus.SUBMITTED:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposerStatus must be submitted or lower to execute a group"
            )

        self.submit(client)
        resp = transaction.wait_for_confirmation(
            client, self.tx_ids[0], wait_rounds
        )
        self.status = AtomicTransactionComposerStatus.COMMITTED

        confirmed_round = resp["confirmed-round"]
        method_results = []

        for i, tx_id in enumerate(self.tx_ids):
            raw_value = None
            return_value = None
            decode_error = None

            if i not in self.method_dict:
                continue
            # Return is void
            if self.method_dict[i].returns.type == abi.Returns.VOID:
                method_results.append(
                    ABIResult(
                        tx_id=tx_id,
                        raw_value=raw_value,
                        return_value=return_value,
                        decode_error=decode_error,
                    )
                )
                continue

            # Parse log for ABI method return value
            try:
                resp = client.pending_transaction_info(tx_id)
                confirmed_round = resp["confirmed-round"]
                logs = resp["logs"] if "logs" in resp else []

                # Look for the last returned value in the log
                for result in reversed(logs):
                    # Check that the first four bytes is the hash of "return"
                    result_bytes = base64.b64decode(result)
                    if result_bytes[:4] != ABI_RETURN_HASH:
                        continue
                    raw_value = result_bytes[4:]
                    return_value = self.method_dict[i].returns.type.decode(
                        raw_value
                    )
                    decode_error = None
                    break
            except Exception as e:
                decode_error = e

            abi_result = ABIResult(
                tx_id=tx_id,
                raw_value=raw_value,
                return_value=return_value,
                decode_error=decode_error,
            )
            method_results.append(abi_result)

        return AtomicTransactionResponse(
            confirmed_round=confirmed_round,
            tx_ids=self.tx_ids,
            results=method_results,
        )


class TransactionSigner(ABC):
    """
    Represents an object which can sign transactions from an atomic transaction group.
    """

    def __init__(self) -> None:
        pass

    @abstractmethod
    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> list:
        pass


class AccountTransactionSigner(TransactionSigner):
    """
    Represents a Transaction Signer for an account that can sign transactions from an
    atomic transaction group.

    Args:
        private_key (str): private key of signing account
    """

    def __init__(self, private_key: str) -> None:
        super().__init__()
        self.private_key = private_key

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> list:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of encoded signed transactions. The length of the
        array will be the same as the length of indexesToSign, and each index i in the array
        corresponds to the signed transaction from txnGroup[indexesToSign[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction group that should be signed
        """
        stxns = []
        for i in indexes:
            stxn = txn_group[i].sign(self.private_key)
            stxns.append(stxn)
        return stxns


class LogicSigTransactionSigner(TransactionSigner):
    """
    Represents a Transaction Signer for a LogicSig that can sign transactions from an
    atomic transaction group.

    Args:
        lsig (LogicSigAccount): LogicSig account
    """

    def __init__(self, lsig: transaction.LogicSigAccount) -> None:
        super().__init__()
        self.lsig = lsig

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> list:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of encoded signed transactions. The length of the
        array will be the same as the length of indexesToSign, and each index i in the array
        corresponds to the signed transaction from txnGroup[indexesToSign[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction group that should be signed
        """
        stxns = []
        for i in indexes:
            stxn = transaction.LogicSigTransaction(txn_group[i], self.lsig)
            stxns.append(stxn)
        return stxns


class MultisigTransactionSigner(TransactionSigner):
    """
    Represents a Transaction Signer for a Multisig that can sign transactions from an
    atomic transaction group.

    Args:
        msig (Multisig): Multisig account
        sks (str): private keys of multisig
    """

    def __init__(self, msig: transaction.Multisig, sks: str) -> None:
        super().__init__()
        self.msig = msig
        self.sks = sks

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> list:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of encoded signed transactions. The length of the
        array will be the same as the length of indexesToSign, and each index i in the array
        corresponds to the signed transaction from txnGroup[indexesToSign[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction group that should be signed
        """
        stxns = []
        for i in indexes:
            mtxn = transaction.MultisigTransaction(txn_group[i], self.msig)
            for sk in self.sks:
                mtxn.sign(sk)
            stxns.append(mtxn)
        return stxns


class TransactionWithSigner:
    def __init__(
        self, txn: transaction.Transaction, signer: TransactionSigner
    ) -> None:
        self.txn = txn
        self.signer = signer


class ABIResult:
    def __init__(
        self,
        tx_id: int,
        raw_value: bytes,
        return_value: Any,
        decode_error: error,
    ) -> None:
        self.tx_id = tx_id
        self.raw_value = raw_value
        self.return_value = return_value
        self.decode_error = decode_error


class AtomicTransactionResponse:
    def __init__(
        self, confirmed_round: int, tx_ids: List[str], results: ABIResult
    ) -> None:
        self.confirmed_round = confirmed_round
        self.tx_ids = tx_ids
        self.abi_results = results
