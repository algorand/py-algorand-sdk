from abc import ABC, abstractmethod
import base64
import copy
from enum import IntEnum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from algosdk import abi, error, transaction
from algosdk.transaction import GenericSignedTransaction
from algosdk.abi.address_type import AddressType
from algosdk.v2client import algod, models


# The first four bytes of an ABI method call return must have this hash
ABI_RETURN_HASH = b"\x15\x1f\x7c\x75"
# Support for generic typing
T = TypeVar("T")


def populate_foreign_array(
    value_to_add: T, foreign_array: List[T], zero_value: Optional[T] = None
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
    if zero_value is not None and value_to_add == zero_value:
        return 0

    offset = 0 if zero_value is None else 1

    if value_to_add in foreign_array:
        return foreign_array.index(value_to_add) + offset

    foreign_array.append(value_to_add)
    return offset + len(foreign_array) - 1


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


class TransactionSigner(ABC):
    """
    Represents an object which can sign transactions from an atomic transaction group.
    """

    def __init__(self) -> None:
        pass

    @abstractmethod
    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> List[GenericSignedTransaction]:
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
    ) -> List[GenericSignedTransaction]:
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
    ) -> List[GenericSignedTransaction]:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of encoded signed transactions. The length of the
        array will be the same as the length of indexesToSign, and each index i in the array
        corresponds to the signed transaction from txnGroup[indexesToSign[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction group that should be signed
        """
        stxns: List[GenericSignedTransaction] = []
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

    def __init__(self, msig: transaction.Multisig, sks: List[str]) -> None:
        super().__init__()
        self.msig = msig
        self.sks = sks

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> List[GenericSignedTransaction]:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of encoded signed transactions. The length of the
        array will be the same as the length of indexesToSign, and each index i in the array
        corresponds to the signed transaction from txnGroup[indexesToSign[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction group that should be signed
        """
        stxns: List[GenericSignedTransaction] = []
        for i in indexes:
            mtxn = transaction.MultisigTransaction(txn_group[i], self.msig)
            for sk in self.sks:
                mtxn.sign(sk)
            stxns.append(mtxn)
        return stxns


class EmptySigner(TransactionSigner):
    def __init__(self) -> None:
        super().__init__()

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> List[GenericSignedTransaction]:
        stxns: List[GenericSignedTransaction] = []
        for i in indexes:
            stxns.append(transaction.SignedTransaction(txn_group[i], ""))
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
        tx_id: str,
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


class SimulateABIResult(ABIResult):
    def __init__(
        self,
        tx_id: str,
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


class SimulateEvalOverrides:
    def __init__(
        self,
        *,
        max_log_calls: Optional[int] = None,
        max_log_size: Optional[int] = None,
        allow_empty_signatures: Optional[bool] = None,
        allow_unnamed_resources: Optional[bool] = None,
        extra_opcode_budget: Optional[int] = None,
    ) -> None:
        self.max_log_calls = max_log_calls
        self.max_log_size = max_log_size
        self.allow_empty_signatures = allow_empty_signatures
        self.allow_unnamed_resources = allow_unnamed_resources
        self.extra_opcode_budget = extra_opcode_budget

    @staticmethod
    def from_simulation_result(
        simulation_result: Dict[str, Any]
    ) -> Optional["SimulateEvalOverrides"]:
        if "eval-overrides" not in simulation_result:
            return None

        eval_override_dict = simulation_result.get("eval-overrides", dict())
        eval_override = SimulateEvalOverrides()

        if "max-log-calls" in eval_override_dict:
            eval_override.max_log_calls = eval_override_dict["max-log-calls"]
        if "max-log-size" in eval_override_dict:
            eval_override.max_log_size = eval_override_dict["max-log-size"]
        if "allow-empty-signatures" in eval_override_dict:
            eval_override.allow_empty_signatures = eval_override_dict[
                "allow-empty-signatures"
            ]
        if "allow-unnamed-resources" in eval_override_dict:
            eval_override.allow_unnamed_resources = eval_override_dict[
                "allow-unnamed-resources"
            ]
        if "extra-opcode-budget" in eval_override_dict:
            eval_override.extra_opcode_budget = eval_override_dict[
                "extra-opcode-budget"
            ]

        return eval_override


class SimulateAtomicTransactionResponse:
    def __init__(
        self,
        version: int,
        failure_message: str,
        failed_at: Optional[List[int]],
        simulate_response: Dict[str, Any],
        tx_ids: List[str],
        results: List[SimulateABIResult],
        eval_overrides: Optional[SimulateEvalOverrides] = None,
        exec_trace_config: Optional[models.SimulateTraceConfig] = None,
    ) -> None:
        self.version = version
        self.failure_message = failure_message
        self.failed_at = failed_at
        self.simulate_response = simulate_response
        self.tx_ids = tx_ids
        self.abi_results = results
        self.eval_overrides = eval_overrides
        self.exec_trace_config = exec_trace_config


class AtomicTransactionComposer:
    """
    Constructs an atomic transaction group which may contain a combination of
    Transactions and ABI Method calls.

    Args:
        status (AtomicTransactionComposerStatus): IntEnum representing the current state of the composer
        method_dict (dict): dictionary of an index in the transaction list to a Method object
        txn_list (list[TransactionWithSigner]): list of transactions with signers
        signed_txns (list[GenericSignedTransaction]): list of signed transactions
        tx_ids (list[str]): list of individual transaction IDs in this atomic group
    """

    # The maximum size of an atomic transaction group.
    MAX_GROUP_SIZE = 16
    # The maximum number of app-args that can be individually packed for ABIs
    MAX_APP_ARG_LIMIT = 16

    def __init__(self) -> None:
        self.status: AtomicTransactionComposerStatus = (
            AtomicTransactionComposerStatus.BUILDING
        )
        self.method_dict: Dict[int, abi.Method] = {}
        self.txn_list: List[TransactionWithSigner] = []
        self.signed_txns: List[GenericSignedTransaction] = []
        self.tx_ids: List[str] = []

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
        self, txn_and_signer: TransactionWithSigner
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
        signer: TransactionSigner,
        method_args: Optional[List[Union[Any, TransactionWithSigner]]] = None,
        on_complete: transaction.OnComplete = transaction.OnComplete.NoOpOC,
        local_schema: Optional[transaction.StateSchema] = None,
        global_schema: Optional[transaction.StateSchema] = None,
        approval_program: Optional[bytes] = None,
        clear_program: Optional[bytes] = None,
        extra_pages: int = 0,
        accounts: Optional[List[str]] = None,
        foreign_apps: Optional[List[int]] = None,
        foreign_assets: Optional[List[int]] = None,
        note: Optional[bytes] = None,
        lease: Optional[bytes] = None,
        rekey_to: Optional[str] = None,
        boxes: Optional[List[Tuple[int, bytes]]] = None,
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
        raw_values: List[Any] = []
        raw_types = []
        txn_list = []

        # First app arg must be the selector of the method
        app_args.append(method.get_selector())

        # Iterate through the method arguments and either pack a transaction
        # or encode a ABI value.
        for i, arg in enumerate(method.args):
            if abi.is_abi_transaction_type(arg.type):
                if not isinstance(method_args[i], TransactionWithSigner):
                    raise error.AtomicTransactionComposerError(
                        "expected TransactionWithSigner as method argument, "
                        f"but received: {method_args[i]}"
                    )

                if not abi.check_abi_transaction_type(
                    arg.type, method_args[i].txn
                ):
                    raise error.AtomicTransactionComposerError(
                        f"expected Transaction type {arg.type} as method argument, "
                        f"but received: {method_args[i].txn.type}"
                    )
                txn_list.append(method_args[i])
            else:
                if abi.is_abi_reference_type(arg.type):
                    current_type: Union[str, abi.ABIType] = abi.UintType(8)
                    if arg.type == abi.ABIReferenceType.ACCOUNT:
                        address_type = AddressType()
                        account_arg = address_type.decode(
                            address_type.encode(
                                cast(Union[str, bytes], method_args[i])
                            )
                        )
                        current_arg: Any = populate_foreign_array(
                            account_arg, accounts, sender
                        )
                    elif arg.type == abi.ABIReferenceType.ASSET:
                        asset_arg = int(cast(int, method_args[i]))
                        current_arg = populate_foreign_array(
                            asset_arg, foreign_assets
                        )
                    elif arg.type == abi.ABIReferenceType.APPLICATION:
                        app_arg = int(cast(int, method_args[i]))
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

    def build_group(self) -> List[TransactionWithSigner]:
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

    def gather_signatures(self) -> List[GenericSignedTransaction]:
        """
        Obtain signatures for each transaction in this group. If signatures have already been obtained,
        this method will return cached versions of the signatures.
        The composer's status will be at least SIGNED after executing this method.
        An error will be thrown if signing any of the transactions fails.

        Returns:
            List[GenericSignedTransaction]: list of signed transactions
        """
        if self.status >= AtomicTransactionComposerStatus.SIGNED:
            # Return cached versions of the signatures
            return self.signed_txns

        stxn_list: List[Optional[GenericSignedTransaction]] = [None] * len(
            self.txn_list
        )
        signer_indexes: Dict[
            TransactionSigner, List[int]
        ] = {}  # Map a signer to a list of indices to sign
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
        full_stxn_list = cast(List[GenericSignedTransaction], stxn_list)

        self.status = AtomicTransactionComposerStatus.SIGNED
        self.signed_txns = full_stxn_list
        return self.signed_txns

    def submit(self, client: algod.AlgodClient) -> List[str]:
        """
        Send the transaction group to the network, but don't wait for it to be
        committed to a block. An error will be thrown if submission fails.
        The composer's status must be SUBMITTED or lower before calling this method.
        If submission is successful, this composer's status will update to SUBMITTED.

        Note: a group can only be submitted again if it fails.

        Args:
            client (AlgodClient): Algod V2 client

        Returns:
            List[str]: list of submitted transaction IDs
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

    def simulate(
        self,
        client: algod.AlgodClient,
        request: Optional[models.SimulateRequest] = None,
    ) -> SimulateAtomicTransactionResponse:
        """
        Send the transaction group to the `simulate` endpoint and wait for results.
        An error will be thrown if submission or execution fails.
        The composer's status must be SUBMITTED or lower before calling this method,
        since execution is only allowed once.

        Args:
            client (AlgodClient): Algod V2 client
            request (models.SimulateRequest): SimulateRequest with options in simulation.
                The request's transaction group will be overrwritten by the composer's group, only simulation related options will be used.

        Returns:
            SimulateAtomicTransactionResponse: Object with simulation results for this
                transaction group, a list of txIDs of the simulated transactions,
                an array of results for each method call transaction in this group.
                If a method has no return value (void), then the method results array
                will contain None for that method's return value.
        """

        if self.status <= AtomicTransactionComposerStatus.SUBMITTED:
            self.gather_signatures()
        else:
            raise error.AtomicTransactionComposerError(
                "AtomicTransactionComposerStatus must be submitted or "
                "lower to simulate a group"
            )

        current_simulation_request = (
            request if request else models.SimulateRequest(txn_groups=list())
        )
        current_simulation_request.txn_groups = [
            models.SimulateRequestTransactionGroup(txns=self.signed_txns)
        ]

        simulation_result = cast(
            Dict[str, Any],
            client.simulate_transactions(current_simulation_request),
        )

        # Only take the first group in the simulate response
        txn_group: Dict[str, Any] = simulation_result["txn-groups"][0]

        # Parse out abi results
        txn_results = [t["txn-result"] for t in txn_group["txn-results"]]
        method_results: List[ABIResult] = []
        for method_index, method in self.method_dict.items():
            tx_id = self.tx_ids[method_index]
            tx_info = txn_results[method_index]
            result: ABIResult = ABIResult(
                tx_id=tx_id,
                raw_value=bytes(),
                return_value=None,
                decode_error=None,
                tx_info=tx_info,
                method=method,
            )
            try:
                result = self.parse_result(
                    method, self.tx_ids[method_index], tx_info
                )
            except Exception as e:
                result.decode_error = e
            method_results.append(result)

        # build up data structure with fields we'd want
        sim_results = []
        for idx, result in enumerate(method_results):
            sim_results.append(
                SimulateABIResult(
                    tx_id=result.tx_id,
                    raw_value=result.raw_value,
                    return_value=result.return_value,
                    decode_error=result.decode_error,
                    tx_info=result.tx_info,
                    method=result.method,
                )
            )

        exec_trace_config: Optional[models.SimulateTraceConfig] = (
            None
            if "exec-trace-config" not in simulation_result
            else models.SimulateTraceConfig.undictify(
                simulation_result["exec-trace-config"]
            )
        )

        return SimulateAtomicTransactionResponse(
            version=simulation_result.get("version", 0),
            failure_message=txn_group.get("failure-message", ""),
            failed_at=txn_group.get("failed-at"),
            simulate_response=simulation_result,
            tx_ids=self.tx_ids,
            results=sim_results,
            eval_overrides=SimulateEvalOverrides.from_simulation_result(
                simulation_result
            ),
            exec_trace_config=exec_trace_config,
        )

    def execute(
        self, client: algod.AlgodClient, wait_rounds: int
    ) -> AtomicTransactionResponse:
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
        method_results: List[ABIResult] = []

        for method_index, method in self.method_dict.items():
            tx_id = self.tx_ids[method_index]
            result: ABIResult = ABIResult(
                tx_id=tx_id,
                raw_value=bytes(),
                return_value=None,
                decode_error=None,
                tx_info={},
                method=method,
            )
            try:
                tx_info = cast(
                    Dict[str, Any], client.pending_transaction_info(tx_id)
                )
                result = self.parse_result(
                    method, self.tx_ids[method_index], tx_info
                )
            except Exception as e:
                result.decode_error = e
            method_results.append(result)

        return AtomicTransactionResponse(
            confirmed_round=confirmed_round,
            tx_ids=self.tx_ids,
            results=method_results,
        )

    def parse_result(
        self, method: abi.Method, txid: str, txn: Dict[str, Any]
    ) -> ABIResult:
        tx_id = txid
        raw_value = bytes()
        return_value = None
        decode_error = None
        try:
            if method.returns.type == abi.Returns.VOID:
                return ABIResult(
                    tx_id=tx_id,
                    raw_value=raw_value,
                    return_value=return_value,
                    decode_error=decode_error,
                    tx_info=txn,
                    method=method,
                )

            logs = txn["logs"] if "logs" in txn else []

            # Look for the last returned value in the log
            if not logs:
                raise error.AtomicTransactionComposerError(
                    "app call transaction did not log a return value"
                )
            result = logs[-1]
            # Check that the first four bytes is the hash of "return"
            result_bytes = base64.b64decode(result)
            if len(result_bytes) < 4 or result_bytes[:4] != ABI_RETURN_HASH:
                raise error.AtomicTransactionComposerError(
                    "app call transaction did not log a return value"
                )
            raw_value = result_bytes[4:]
            method_return_type = cast(abi.ABIType, method.returns.type)
            return_value = method_return_type.decode(raw_value)
        except Exception as e:
            decode_error = e

        return ABIResult(
            tx_id=tx_id,
            raw_value=raw_value,
            return_value=return_value,
            decode_error=decode_error,
            tx_info=txn,
            method=method,
        )
