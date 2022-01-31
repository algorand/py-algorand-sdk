from typing import List


class DryrunResponse:
    def __init__(self, drrjson):
        self.error = drrjson["error"]
        self.protocol = drrjson["protocol-version"]
        self.txns = [DryrunTransactionResult(txn) for txn in drrjson["txns"]]


class DryrunTransactionResult:
    def __init__(self, dr):
        if "disassembly" in dr:
            self.disassembly = dr["disassembly"]
        if "app-call-messages" in dr:
            self.app_call_messages = dr["app-call-messages"]
        if "app-call-trace" in dr:
            self.app_call_trace = DryrunTrace(dr["app-call-trace"])
        if "local-deltas" in dr:
            self.local_deltas = dr["local-deltas"]
        if "global-delta" in dr:
            self.global_delta = dr["global-delta"]
        if "cost" in dr:
            self.app_call_cost = dr["cost"]
        if "logic-sig-messages" in dr:
            self.logic_sig_messages = dr["logic-sig-messages"]
        if "logic-sig-trace" in dr:
            self.logic_sig_trace = DryrunTrace(dr["logic-sig-trace"])
        if "logs" in dr:
            self.logs = dr["logs"]

    def app_trace(self):
        lines = []
        for line in self.app_call_trace.get_trace():
            src_line = self.disassembly[line[0] - 1]
            lines.append(
                "{}{}\t{}".format(
                    src_line, " " * (16 - len(src_line)), line[1]
                )
            )
        return "\n".join(lines)

    def lsig_trace(self):
        lines = []
        for line in self.logic_sig_trace.get_trace():
            src_line = self.disassembly[line[0] - 1]
            lines.append(
                "{}{}\t{}".format(
                    src_line, " " * (16 - len(src_line)), line[1]
                )
            )
        return "\n".join(lines)


class DryrunTrace:
    def __init__(self, trace):
        self.trace = [DryrunTraceLine(line) for line in trace]

    def get_trace(self) -> List[str]:
        return [line.trace_line() for line in self.trace]


class DryrunTraceLine:
    def __init__(self, tl):
        self.line = tl["line"]
        self.pc = tl["pc"]
        self.stack = [DryrunStackValue(sv) for sv in tl["stack"]]

    def trace_line(self):
        return (self.line, [sv.__str__() for sv in self.stack])


class DryrunStackValue:
    def __init__(self, v):
        self.type = v["type"]
        self.bytes = v["bytes"]
        self.int = v["uint"]

    def __str__(self):
        if self.type == 1:
            return self.bytes
        return self.int
