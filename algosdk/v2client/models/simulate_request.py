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


class SimulateTraceConfig(object):
    enable: bool
    stack_change: bool
    scratch_change: bool

    def __init__(
        self,
        *,
        enable: bool = False,
        stack_change: bool = False,
        scratch_change: bool = False,
    ) -> None:
        self.enable = enable
        self.stack_change = stack_change
        self.scratch_change = scratch_change

    def dictify(self) -> Dict[str, Any]:
        return {
            "enable": self.enable,
            "stack-change": self.stack_change,
            "scratch-change": self.scratch_change,
        }


class SimulateRequest(object):
    txn_groups: List[SimulateRequestTransactionGroup]
    allow_more_logs: bool
    allow_empty_signatures: bool
    extra_opcode_budget: int
    exec_trace_config: SimulateTraceConfig

    def __init__(
        self,
        *,
        txn_groups: List[SimulateRequestTransactionGroup],
        allow_more_logs: bool = False,
        allow_empty_signatures: bool = False,
        extra_opcode_budget: int = 0,
        exec_trace_config: SimulateTraceConfig = SimulateTraceConfig(),
    ) -> None:
        self.txn_groups = txn_groups
        self.allow_more_logs = allow_more_logs
        self.allow_empty_signatures = allow_empty_signatures
        self.extra_opcode_budget = extra_opcode_budget
        self.exec_trace_config = exec_trace_config

    def dictify(self) -> Dict[str, Any]:
        return {
            "txn-groups": [
                txn_group.dictify() for txn_group in self.txn_groups
            ],
            "allow-more-logging": self.allow_more_logs,
            "allow-empty-signatures": self.allow_empty_signatures,
            "extra-opcode-budget": self.extra_opcode_budget,
            "exec-trace-config": self.exec_trace_config.dictify(),
        }
