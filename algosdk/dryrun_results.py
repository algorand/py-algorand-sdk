import base64
from typing import List
import tabulate as tlib
from tabulate import tabulate, TableFormat, DataRow


tlib.MIN_PADDING = 0


class StackPrinterConfig:
    DEFAULT_MAX_WIDTH: int = 30

    def __init__(self, max_width=DEFAULT_MAX_WIDTH, top_of_stack_first=True):
        self.max_width = max_width
        self.top_of_stack_first = top_of_stack_first


class DryrunResponse:
    def __init__(self, drrjson: dict):
        for param in ["error", "protocol-version", "txns"]:
            assert (
                param in drrjson
            ), f"expecting dryrun response object to have key '{param}' but it is missing"

        # These are all required fields
        self.error = drrjson["error"]
        self.protocol = drrjson["protocol-version"]
        self.txns = [DryrunTransactionResult(txn) for txn in drrjson["txns"]]


class DryrunTransactionResult:
    def __init__(self, dr):
        assert (
            "disassembly" in dr
        ), "expecting dryrun transaction result to have key 'disassembly' but its missing"

        self.disassembly = dr["disassembly"]

        optionals = [
            "app-call-messages",
            "local-deltas",
            "global-delta",
            "cost",
            "logic-sig-messages",
            "logic-sig-disassembly",
            "logs",
        ]
        def attrname(field):
            return field.replace("-","_")
            
        for field in optionals:
            setattr(self, attrname(field), dr.get(field))

        traces = ["app-call-trace", "logic-sig-trace"]
        for trace_field in traces:
            if trace_field in dr:
                setattr(
                    self,
                    trace_field.replace("-", "_"),
                    DryrunTrace(dr[trace_field]),
                )

    def app_call_rejected(self) -> bool:
        return False if self.app_call_messages is None else "REJECT" in self.app_call_messages

    def logic_sig_rejected(self) -> bool:
        if self.logic_sig_messages is not None:
            return "REJECT" in self.logic_sig_messages
        return False

    @classmethod
    def trace(
        cls,
        dr_trace: "DryrunTrace",
        disassembly: List[str],
        spc: StackPrinterConfig,
    ) -> str:

        # 16 for length of the header up to spaces
        headers = ["pc#", "ln#", "source", "scratch", "stack"]
        lines = []
        for idx in range(len(dr_trace.trace)):

            trace_line = dr_trace.trace[idx]

            src = disassembly[trace_line.line]
            if trace_line.error != "":
                src = "!! {} !!".format(trace_line.error)

            prev_scratch = []
            if idx > 0:
                prev_scratch = dr_trace.trace[idx - 1].scratch

            scratch = scratch_to_string(prev_scratch, trace_line.scratch)
            stack = stack_to_string(trace_line.stack, spc.top_of_stack_first)
            lines.append(
                [
                    "{}".format(trace_line.pc),
                    "{}".format(trace_line.line),
                    truncate(src, spc.max_width),
                    truncate(scratch, spc.max_width),
                    truncate(stack, spc.max_width),
                ]
            )

        return (
            tabulate(
                lines,
                headers,
                disable_numparse=True,
                tablefmt=TableFormat(
                    headerrow=DataRow("", " |", ""),
                    datarow=DataRow("", " |", ""),
                    padding=0,
                    lineabove=None,
                    linebelowheader=None,
                    linebetweenrows=None,
                    linebelow=None,
                    with_header_hide=None,
                ),
            )
            + "\n"
        )

    def app_trace(self, spc: StackPrinterConfig = None) -> str:
        if not hasattr(self, "app_call_trace"):
            return ""

        if spc == None:
            spc = StackPrinterConfig(top_of_stack_first=False)

        return self.trace(self.app_call_trace, self.disassembly, spc=spc)

    def lsig_trace(self, spc: StackPrinterConfig = None) -> str:
        if not hasattr(self, "logic_sig_trace"):
            return ""

        if (
            not hasattr(self, "logic_sig_disassembly")
            or self.logic_sig_disassembly is None
        ):
            return ""

        if spc == None:
            spc = StackPrinterConfig(top_of_stack_first=False)

        return self.trace(
            self.logic_sig_trace, self.logic_sig_disassembly, spaces=spc
        )


class DryrunTrace:
    def __init__(self, trace: List[dict]):
        self.trace = [DryrunTraceLine(line) for line in trace]

    def get_trace(self) -> List[str]:
        return [line.trace_line() for line in self.trace]


class DryrunTraceLine:
    def __init__(self, tl):
        self.line = tl["line"]
        self.pc = tl["pc"]

        self.error = ""
        if "error" in tl:
            self.error = tl["error"]

        self.scratch = []
        if "scratch" in tl:
            self.scratch = [DryrunStackValue(sv) for sv in tl["scratch"]]

        self.stack = [DryrunStackValue(sv) for sv in tl["stack"]]


class DryrunStackValue:
    def __init__(self, v):
        self.type = v["type"]
        self.bytes = v["bytes"]
        self.int = v["uint"]

    def __str__(self) -> str:
        if len(self.bytes) > 0:
            return "0x" + base64.b64decode(self.bytes).hex()
        return str(self.int)

    def __eq__(self, other: "DryrunStackValue"):
        return (
            self.type == other.type
            and self.bytes == other.bytes
            and self.int == other.int
        )


def truncate(s: str, max_width: int) -> str:
    if len(s) > max_width and max_width > 0:
        return s[:max_width] + "..."
    return s


def scratch_to_string(
    prev_scratch: List[DryrunStackValue], curr_scratch: List[DryrunStackValue]
) -> str:
    if len(curr_scratch) == 0:
        return ""

    new_idx = None
    for idx in range(len(curr_scratch)):
        if idx >= len(prev_scratch):
            new_idx = idx
            continue

        if curr_scratch[idx] != prev_scratch[idx]:
            new_idx = idx

    if new_idx == None:
        return ""

    return "{} = {}".format(new_idx, str(curr_scratch[new_idx]))


def stack_to_string(stack: List[DryrunStackValue], reverse: bool) -> str:
    if reverse:
        stack.reverse()
    return "[{}]".format(", ".join([str(sv) for sv in stack]))