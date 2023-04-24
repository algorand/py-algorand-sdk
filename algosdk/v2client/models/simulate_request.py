from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from algosdk import transaction


class SimulateRequestTransactionGroup(object):
    txns: "List[transaction.GenericSignedTransaction]"

    def __init__(
        self, *, txns: "List[transaction.GenericSignedTransaction]"
    ) -> None:
        self.txns = txns

    def dictify(self) -> Dict[str, Any]:
        return {"txns": [txn.dictify() for txn in self.txns]}


class SimulateRequest(object):
    txn_groups: List[SimulateRequestTransactionGroup]
    lift_lot_limits: bool

    def __init__(
        self,
        *,
        txn_groups: List[SimulateRequestTransactionGroup],
        lift_log_limits: bool = False,
    ) -> None:
        self.txn_groups = txn_groups
        self.lift_lot_limits = lift_log_limits

    def dictify(self) -> Dict[str, Any]:
        return {
            "txn-groups": [
                txn_group.dictify() for txn_group in self.txn_groups
            ],
            "lift-log-limits": self.lift_lot_limits,
        }
