from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from algosdk import transaction


class SimulateRequestTransactionGroup(object):
    txns: "list[transaction.GenericSignedTransaction]"

    def __init__(
        self, *, txns: "list[transaction.GenericSignedTransaction]"
    ) -> None:
        self.txns = txns

    def dictify(self) -> dict:
        return {"txns": [txn.dictify() for txn in self.txns]}


class SimulateRequest(object):
    txn_groups: list[SimulateRequestTransactionGroup]

    def __init__(
        self, *, txn_groups: list[SimulateRequestTransactionGroup]
    ) -> None:
        self.txn_groups = txn_groups

    def dictify(self) -> dict:
        return {
            "txn-groups": [
                txn_group.dictify() for txn_group in self.txn_groups
            ]
        }
