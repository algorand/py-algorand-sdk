import base64
import copy
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, List, Optional, Tuple, TypeVar, Union

from algosdk import abi, error
from algosdk.abi.address_type import AddressType
from algosdk.future import transaction
from algosdk.v2client import algod

# The first four bytes of an ABI method call return must have this hash
ABI_RETURN_HASH = b"\x15\x1f\x7c\x75"
# Support for generic typing
T = TypeVar("T")


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


def populate_foreign_array(
    value_to_add: T, foreign_array: List[T], zero_value: T = None
) -> int:
    """
    Add a value to an application call's foreign array. The addition will be as
    compact as possible, and this function will return an index used to
    reference `value_to_add` in the `foreign_array`.

    Args:
        value_to_add: value to add to the array. If the value is already
            present, it will not be added again. Instead, the existing index
            will be returned.
        foreign_array: the existing foreign array. This input may be modified
            to append `value_to_add`.
        zero_value: If provided, this value indicates two things: the 0 value is
            reserved for this array so `foreign_array` must start at index 1;
            additionally, if `value_to_add` equals `zero_value`, then
            `value_to_add` will not be added to the array and the 0 index will
            be returned.
    """
    if zero_value and value_to_add == zero_value:
        return 0

    offset = 0 if not zero_value else 1

    if value_to_add in foreign_array:
        return foreign_array.index(value_to_add) + offset

    foreign_array.append(value_to_add)
    return offset + len(foreign_array) - 1


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
    MAX_APP_ARG_LIMIT = 16

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
        method: abi.Method,
        sender: str,
        sp: transaction.SuggestedParams,
        signer: "TransactionSigner",
        method_args: List[Union[Any, "TransactionWithSigner"]] = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        local_schema: transaction.StateSchema = None,
        global_schema: transaction.StateSchema = None,
        approval_program: bytes = None,
        clear_program: bytes = None,
        extra_pages: int = None,
        accounts: List[str] = None,
        foreign_apps: List[int] = None,
        foreign_assets: List[int] = None,
        note: bytes = None,
        lease: bytes = None,
        rekey_to: str = None,
        boxes: List[Tuple[int, bytes]] = None,
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
            local_schema (StateSchema, optional): restricts what can be stored by created application;
                must be omitted if not creating an application
            global_schema (StateSchema, optional): restricts what can be stored by created application;
                must be omitted if not creating an application
            approval_program (bytes, optional): the program to run on transaction approval;
                must be omitted if not creating or updating an application
            clear_program (bytes, optional): the program to run when state is being cleared;
                must be omitted if not creating or updating an application
            extra_pages (int, optional): additional program space for supporting larger programs.
                A page is 1024 bytes.
            accounts (list[string], optional): list of additional accounts involved in call
            foreign_apps (list[int], optional): list of other applications (identified by index) involved in call
            foreign_assets (list[int], optional): list of assets involved in call
            note (bytes, optional): arbitrary optional bytes
            lease (byte[32], optional): specifies a lease, and no other transaction
                with the same sender and lease can be confirmed in this
                transaction's valid rounds
            rekey_to (str, optional): additionally rekey the sender to this address
            boxes (list[(int, bytes)], optional): list of tuples specifying app id and key for boxes the app may access

        """
        if self.status != AtomicTransactionComposerStatus.BUILDING:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer must be in BUILDING state for a transaction to be added"
            )
        if len(self.txn_list) + method.get_txn_calls() > self.MAX_GROUP_SIZE:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposer cannot exceed MAX_GROUP_SIZE transactions"
            )
        if app_id == 0:
            if not approval_program or not clear_program:
                raise error.AtomicTransactionComposerError(
                    "One of the following required parameters for application creation is missing: approvalProgram, clearProgram"
                )
        elif on_complete == transaction.OnComplete.UpdateApplicationOC:
            if not approval_program or not clear_program:
                raise error.AtomicTransactionComposerError(
                    "One of the following required parameters for OnApplicationComplete.UpdateApplicationOC is missing: approvalProgram, clearProgram"
                )
            if local_schema or global_schema or extra_pages:
                raise error.AtomicTransactionComposerError(
                    "One of the following application creation parameters were set on a non-creation call: numGlobalInts, numGlobalByteSlices, numLocalInts, numLocalByteSlices, extraPages"
                )
        elif (
            approval_program
            or clear_program
            or local_schema
            or global_schema
            or extra_pages
        ):
            raise error.AtomicTransactionComposerError(
                "One of the following application creation parameters were set on a non-creation call: approvalProgram, clearProgram, numGlobalInts, numGlobalByteSlices, numLocalInts, numLocalByteSlices, extraPages"
            )
        if not method_args:
            method_args = []
        if len(method.args) != len(method_args):
            raise error.AtomicTransactionComposerError(
                "number of method arguments do not match the method signature"
            )
        if not isinstance(method, abi.Method):
            raise error.AtomicTransactionComposerError(
                "invalid Method object was passed into AtomicTransactionComposer"
            )

        # Initialize foreign object maps
        accounts = accounts[:] if accounts else []
        foreign_apps = foreign_apps[:] if foreign_apps else []
        foreign_assets = foreign_assets[:] if foreign_assets else []
        boxes = boxes[:] if boxes else []

        app_args = []
        raw_values = []
        raw_types = []
        txn_list = []

        # First app arg must be the selector of the method
        app_args.append(method.get_selector())

        # Iterate through the method arguments and either pack a transaction
        # or encode a ABI value.
        for i, arg in enumerate(method.args):
            if abi.is_abi_transaction_type(arg.type):
                if not isinstance(
                    method_args[i], TransactionWithSigner
                ) or not abi.check_abi_transaction_type(
                    arg.type, method_args[i].txn
                ):
                    raise error.AtomicTransactionComposerError(
                        "expected TransactionWithSigner as method argument, but received: {}".format(
                            method_args[i]
                        )
                    )
                txn_list.append(method_args[i])
            else:
                if abi.is_abi_reference_type(arg.type):
                    current_type = abi.UintType(8)
                    if arg.type == abi.ABIReferenceType.ACCOUNT:
                        address_type = AddressType()
                        account_arg = address_type.decode(
                            address_type.encode(method_args[i])
                        )
                        current_arg = populate_foreign_array(
                            account_arg, accounts, sender
                        )
                    elif arg.type == abi.ABIReferenceType.ASSET:
                        asset_arg = int(method_args[i])
                        current_arg = populate_foreign_array(
                            asset_arg, foreign_assets
                        )
                    elif arg.type == abi.ABIReferenceType.APPLICATION:
                        app_arg = int(method_args[i])
                        current_arg = populate_foreign_array(
                            app_arg, foreign_apps, app_id
                        )
                    else:
                        # Shouldn't reach this line unless someone accidentally
                        # adds another foreign array arg
                        raise error.AtomicTransactionComposerError(
                            "cannot recognize {} as a foreign array arg".format(
                                arg.type
                            )
                        )
                else:
                    current_type = arg.type
                    current_arg = method_args[i]

                raw_types.append(current_type)
                raw_values.append(current_arg)

        # Compact the arguments into a single tuple, if there are more than
        # 15 arguments excluding the selector, into the last app arg slot.
        if len(raw_types) > self.MAX_APP_ARG_LIMIT - 1:
            additional_types = raw_types[self.MAX_APP_ARG_LIMIT - 2 :]
            additional_values = raw_values[self.MAX_APP_ARG_LIMIT - 2 :]
            raw_types = raw_types[: self.MAX_APP_ARG_LIMIT - 2]
            raw_values = raw_values[: self.MAX_APP_ARG_LIMIT - 2]
            raw_types.append(abi.TupleType(additional_types))
            raw_values.append(additional_values)

        for i, arg_type in enumerate(raw_types):
            app_args.append(arg_type.encode(raw_values[i]))

        # Create a method call transaction
        method_txn = transaction.ApplicationCallTxn(
            sender=sender,
            sp=sp,
            index=app_id,
            on_complete=on_complete,
            local_schema=local_schema,
            global_schema=global_schema,
            approval_program=approval_program,
            clear_program=clear_program,
            app_args=app_args,
            accounts=accounts,
            foreign_apps=foreign_apps,
            foreign_assets=foreign_assets,
            note=note,
            lease=lease,
            rekey_to=rekey_to,
            extra_pages=extra_pages,
            boxes=boxes,
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
        if len(self.txn_list) > 1:
            group_txns = [t.txn for t in self.txn_list]
            group_id = transaction.calculate_group_id(group_txns)
            for t in self.txn_list:
                t.txn.group = group_id
                self.tx_ids.append(t.txn.get_txid())
        else:
            self.tx_ids.append(self.txn_list[0].txn.get_txid())

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
        self.status = AtomicTransactionComposerStatus.SUBMITTED

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
            tx_info = None

            if i not in self.method_dict:
                continue

            # Parse log for ABI method return value
            try:
                tx_info = client.pending_transaction_info(tx_id)
                if self.method_dict[i].returns.type == abi.Returns.VOID:
                    method_results.append(
                        ABIResult(
                            tx_id=tx_id,
                            raw_value=raw_value,
                            return_value=return_value,
                            decode_error=decode_error,
                            tx_info=tx_info,
                            method=self.method_dict[i],
                        )
                    )
                    continue

                logs = tx_info["logs"] if "logs" in tx_info else []

                # Look for the last returned value in the log
                if not logs:
                    raise error.AtomicTransactionComposerError(
                        "app call transaction did not log a return value"
                    )
                result = logs[-1]
                # Check that the first four bytes is the hash of "return"
                result_bytes = base64.b64decode(result)
                if (
                    len(result_bytes) < 4
                    or result_bytes[:4] != ABI_RETURN_HASH
                ):
                    raise error.AtomicTransactionComposerError(
                        "app call transaction did not log a return value"
                    )
                raw_value = result_bytes[4:]
                return_value = self.method_dict[i].returns.type.decode(
                    raw_value
                )
            except Exception as e:
                decode_error = e

            abi_result = ABIResult(
                tx_id=tx_id,
                raw_value=raw_value,
                return_value=return_value,
                decode_error=decode_error,
                tx_info=tx_info,
                method=self.method_dict[i],
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
        decode_error: Optional[Exception],
        tx_info: dict,
        method: abi.Method,
    ) -> None:
        self.tx_id = tx_id
        self.raw_value = raw_value
        self.return_value = return_value
        self.decode_error = decode_error
        self.tx_info = tx_info
        self.method = method


class AtomicTransactionResponse:
    def __init__(
        self, confirmed_round: int, tx_ids: List[str], results: List[ABIResult]
    ) -> None:
        self.confirmed_round = confirmed_round
        self.tx_ids = tx_ids
        self.abi_results = results
