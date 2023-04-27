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
    allow_more_logs: bool
    allow_empty_signatures: bool

    def __init__(
        self,
        *,
        txn_groups: List[SimulateRequestTransactionGroup],
        allow_more_logs: bool = False,
        allow_empty_signatures: bool = False,
    ) -> None:
        self.txn_groups = txn_groups
        self.allow_more_logs = allow_more_logs
        self.allow_empty_signatures = allow_empty_signatures

    def dictify(self) -> Dict[str, Any]:
        return {
            "txn-groups": [
                txn_group.dictify() for txn_group in self.txn_groups
            ],
            "allow-more-logging": self.allow_more_logs,
            "allow-empty-signatures": self.allow_empty_signatures,
        }
