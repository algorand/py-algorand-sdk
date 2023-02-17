import base64
from typing import Any, Optional, List, Dict
from algosdk import transaction, encoding


class PendingTransactionResponse:
    confirmed_round: Optional[int]
    pool_error: str

    asset_index: Optional[int]
    application_index: Optional[int]

    local_state_delta: List[Any]
    global_state_delta: Dict[str, Any]

    inner_txns: List["PendingTransactionResponse"]
    logs: List[bytes]

    txn: transaction.SignedTransaction

    close_rewards: Optional[int]
    close_amount: Optional[int]
    asset_close_amount: Optional[int]
    receiver_rewards: Optional[int]
    sender_rewards: Optional[int]

    _raw: Dict[str, Any]

    @staticmethod
    def undictify(data: Dict[str, Any]) -> "PendingTransactionResponse":
        ptr = PendingTransactionResponse()
        ptr.txn = encoding.msgpack_decode(data["txn"])
        ptr.logs = data.get("logs", [])
        ptr.pool_error = data.get("pool-error", "")
        ptr.confirmed_round = data.get("confirmed-round", None)
        ptr.asset_index = data.get("asset-index", None)
        ptr.application_index = data.get("application-index", None)
        ptr.local_state_delta = data.get("local-state-delta", [])
        ptr.global_state_delta = data.get("global-state-delta", {})
        ptr.inner_txns = []
        if "inner-txns" in data:
            ptr.inner_txns = [
                PendingTransactionResponse.undictify(itxn)
                for itxn in data["inner-txns"]
            ]
        return ptr

    def dictify(self) -> Dict[str, Any]:
        return {
            "txn": self.txn.dictify(),
            "logs": [base64.b64encode(l) for l in self.logs],
            "pool-error": self.pool_error,
            "confirmed-round": self.confirmed_round,
            "asset-index": self.asset_index,
            "application-index": self.application_index,
            "local-state-delta": self.local_state_delta,
            "global-state-delta": self.global_state_delta,
            "inner-txns": [t.dictify() for t in self.inner_txns],
        }


class SimulationTransactionResult:
    missing_signature: bool
    result: PendingTransactionResponse

    @staticmethod
    def undictify(data: Dict[str, Any]) -> "SimulationTransactionResult":
        s = SimulationTransactionResult()
        s.result = PendingTransactionResponse.undictify(data["txn-result"])
        s.missing_signature = data.get("missing-signature", False)
        return s


class SimulationTransactionGroupResult:
    txn_results: List[SimulationTransactionResult]
    failure_message: str

    # failed_at is "transaction path": e.g. [0, 0, 1] means
    #   the second inner txn of the first inner txn of the first txn.
    failed_at: List[int]

    @staticmethod
    def undictify(data: Dict[str, Any]) -> "SimulationTransactionGroupResult":
        stgr = SimulationTransactionGroupResult()
        stgr.failed_at = data.get("failed-at", [])
        stgr.failure_message = data.get("failure-message", "")
        stgr.txn_results = [
            SimulationTransactionResult.undictify(t)
            for t in data["txn-results"]
        ]
        return stgr


class SimulationResponse:
    version: int
    would_succeed: bool
    txn_groups: List[SimulationTransactionGroupResult]

    @staticmethod
    def undictify(data: Dict[str, Any]) -> "SimulationResponse":
        sr = SimulationResponse()
        sr.version = data["version"]
        sr.would_succeed = data["would-succeed"]
        sr.txn_groups = [
            SimulationTransactionGroupResult.undictify(txn)
            for txn in data["txn-groups"]
        ]
        return sr
