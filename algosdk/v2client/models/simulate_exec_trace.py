from typing import Dict, Any, List

from algosdk.v2client.models import AVMValue


class SimulateExecTrace:
    approval_program_trace: List[AVMValue]
    clear_state_program_trace: List[AVMValue]
    logic_sig_trace: List[AVMValue]
    inner_trace: "List[SimulateExecTrace]"

    def __init__(
        self,
        *,
        approval_program_trace: List[AVMValue],
        clear_state_program_trace: List[AVMValue],
        logic_sig_trace: List[AVMValue],
        inner_trace: "List[SimulateExecTrace]"
    ):
        self.approval_program_trace = approval_program_trace
        self.clear_state_program_trace = clear_state_program_trace
        self.logic_sig_trace = logic_sig_trace
        self.inner_trace = inner_trace

    def dictify(self) -> Dict[str, Any]:
        return {
            "approval-program-trace": self.approval_program_trace,
            "clear-state-program-trace": self.clear_state_program_trace,
            "logic-sig-trace": self.logic_sig_trace,
            "inner-trace": self.inner_trace,
        }
