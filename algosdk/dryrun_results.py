from typing import List
import base64


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
    DEFAULT_TRACE_SPACES: int = 20

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
        for field in optionals:
            if field in dr:
                setattr(self, field.replace("-", "_"), dr[field])

        traces = ["app-call-trace", "logic-sig-trace"]
        for trace_field in traces:
            if trace_field in dr:
                setattr(
                    self,
                    trace_field.replace("-", "_"),
                    DryrunTrace(dr[trace_field]),
                )

    @classmethod
    def trace(
        cls,
        dr_trace: "DryrunTrace",
        disassembly: List[str],
        spaces: int = None,
    ) -> str:
        if spaces is None:
            spaces = cls.DEFAULT_TRACE_SPACES

        # If 0, pad to the lenght of the longest line
        if spaces == 0:
            for line in disassembly:
                if len(line) > spaces:
                    spaces = len(line)

        lines = []
        for line in dr_trace.get_trace():
            # Pad to 4 spaces since we don't expect programs to have > 9999 lines
            line_number_padding = " " * (4 - len(str(line[0])))
            src_line = "{}{} {}".format(
               line_number_padding, line[0],  disassembly[line[0]]
            )
            lines.append(
                "{}{} {}".format(
                    src_line, " " * (spaces - len(src_line)), line[1]
                )
            )

        return "\n".join(lines)

    def app_trace(self, spaces: int = None) -> str:
        if not hasattr(self, "app_call_trace"):
            return ""

        return self.trace(self.app_call_trace, self.disassembly, spaces=spaces)

    def lsig_trace(self, spaces: int = None) -> str:
        if not hasattr(self, "logic_sig_trace"):
            return ""

        # TODO: should be able to take this out when go-algorand#3577 is merged
        dis = self.disassembly
        if hasattr(self, "logic_sig_disassembly"):
            dis = self.logic_sig_disassembly

        return self.trace(
            self.logic_sig_trace, dis, spaces=spaces
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
        self.stack = [DryrunStackValue(sv) for sv in tl["stack"]]

    def trace_line(self):
        return (
            self.line,
            "[" + ", ".join([str(sv) for sv in self.stack]) + "]",
        )


class DryrunStackValue:
    def __init__(self, v):
        self.type = v["type"]
        self.bytes = v["bytes"]
        self.int = v["uint"]

    def __str__(self) -> str:
        if self.type == 1:
            if len(self.bytes) > 0:
                return "0x" + base64.b64decode(self.bytes).hex()
            else:
                "''"
        return str(self.int)
