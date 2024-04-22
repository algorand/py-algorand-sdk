from typing import List, Dict, Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from algosdk import transaction


class SimulateRequestTransactionGroup:
    txns: "List[transaction.GenericSignedTransaction]"

    def __init__(
        self, *, txns: "List[transaction.GenericSignedTransaction]"
    ) -> None:
        self.txns = txns

    def dictify(self) -> Dict[str, Any]:
        return {"txns": [txn.dictify() for txn in self.txns]}


class SimulateTraceConfig:
    enable: bool
    stack_change: bool
    scratch_change: bool
    state_change: bool

    def __init__(
        self,
        *,
        enable: bool = False,
        stack_change: bool = False,
        scratch_change: bool = False,
        state_change: bool = False,
    ) -> None:
        self.enable = enable
        self.stack_change = stack_change
        self.scratch_change = scratch_change
        self.state_change = state_change

    def dictify(self) -> Dict[str, Any]:
        return {
            "enable": self.enable,
            "stack-change": self.stack_change,
            "scratch-change": self.scratch_change,
            "state-change": self.state_change,
        }

    @staticmethod
    def undictify(d: Dict[str, Any]) -> "SimulateTraceConfig":
        return SimulateTraceConfig(
            enable="enable" in d and d["enable"],
            stack_change="stack-change" in d and d["stack-change"],
            scratch_change="scratch-change" in d and d["scratch-change"],
            state_change="state-change" in d and d["state-change"],
        )


class SimulateRequest:
    txn_groups: List[SimulateRequestTransactionGroup]
    allow_more_logs: bool
    allow_empty_signatures: bool
    allow_unnamed_resources: bool
    extra_opcode_budget: int
    exec_trace_config: SimulateTraceConfig
    round: Optional[int]

    def __init__(
        self,
        *,
        txn_groups: List[SimulateRequestTransactionGroup],
        round: Optional[int] = None,
        allow_more_logs: bool = False,
        allow_empty_signatures: bool = False,
        allow_unnamed_resources: bool = False,
        extra_opcode_budget: int = 0,
        exec_trace_config: Optional[SimulateTraceConfig] = None,
    ) -> None:
        self.txn_groups = txn_groups
        self.round = round
        self.allow_more_logs = allow_more_logs
        self.allow_empty_signatures = allow_empty_signatures
        self.allow_unnamed_resources = allow_unnamed_resources
        self.extra_opcode_budget = extra_opcode_budget
        self.exec_trace_config = (
            exec_trace_config if exec_trace_config else SimulateTraceConfig()
        )

    def dictify(self) -> Dict[str, Any]:
        return {
            "txn-groups": [
                txn_group.dictify() for txn_group in self.txn_groups
            ],
            "round": self.round,
            "allow-more-logging": self.allow_more_logs,
            "allow-unnamed-resources": self.allow_unnamed_resources,
            "allow-empty-signatures": self.allow_empty_signatures,
            "extra-opcode-budget": self.extra_opcode_budget,
            "exec-trace-config": self.exec_trace_config.dictify(),
        }
