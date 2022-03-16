from base64 import b64decode
import csv
from dataclasses import dataclass
from enum import Enum
import io
from tabulate import tabulate
from typing import Any, Callable, Dict, List, Tuple, Union

from algosdk.testing.dryrun import assert_error, assert_no_error

# Note: = this type _shadows_ PyTeal's Mode and should  adhere to the same API:
Mode = Enum("Mode", "Signature Application")

DryRunAssertionType = Enum(
    "DryRunAssertionType",
    "cost lastLog finalScratch stackTop maxStackHeight status rejected passed error noError globalStateHas localStateHas",
)
DRA = DryRunAssertionType

from inspect import signature


@dataclass
class TealVal:
    i: int = 0
    b: str = ""
    is_b: bool = None
    hide_empty: bool = True

    @classmethod
    def from_stack(cls, d: dict) -> "TealVal":
        return TealVal(d["uint"], d["bytes"], d["type"] == 1, hide_empty=False)

    @classmethod
    def from_scratch(cls, d: dict) -> "TealVal":
        return TealVal(d["uint"], d["bytes"], len(d["bytes"]) > 0)

    def is_empty(self) -> bool:
        return not (self.i or self.b)

    def __str__(self) -> str:
        if self.hide_empty and self.is_empty():
            return ""

        assert (
            self.is_b is not None
        ), f"can't handle StackVariable with empty type"
        return "0x" + b64decode(self.b).hex() if self.is_b else str(self.i)

    def as_python_type(self) -> Union[int, str, None]:
        if self.is_b is None:
            return None
        return str(self) if self.is_b else self.i


@dataclass
class BlackBoxResults:
    steps_executed: int
    program_counters: List[int]
    teal_line_numbers: List[int]
    teal_source_lines: List[str]
    stack_evolution: List[list]
    scratch_evolution: List[dict]
    final_scratch_state: Dict[int, TealVal]
    slots_used: List[int]
    raw_stacks: List[list]

    def assert_well_defined(self):
        assert all(
            self.steps_executed == len(x)
            for x in (
                self.program_counters,
                self.teal_source_lines,
                self.stack_evolution,
                self.scratch_evolution,
            )
        ), f"some mismatch in trace sizes: all expected to be {self.steps_executed}"

    def __str__(self) -> str:
        return f"BlackBoxResult(steps_executed={self.steps_executed})"

    def steps(self) -> int:
        return self.steps_executed

    def final_stack(self) -> str:
        return self.stack_evolution[-1]

    def final_stack_top(self) -> Union[int, str, None]:
        final_stack = self.raw_stacks[-1]
        if not final_stack:
            return None
        top = final_stack[-1]
        return str(top) if top.is_b else top.i

    def max_stack_height(self) -> int:
        return max(len(s) for s in self.raw_stacks)

    def final_scratch(
        self, with_formatting: bool = False
    ) -> Dict[Union[int, str], Union[int, str]]:
        unformatted = {
            i: str(s) if s.is_b else s.i
            for i, s in self.final_scratch_state.items()
        }
        if not with_formatting:
            return unformatted
        return {f"s@{i:03}": s for i, s in unformatted.items()}

    def slots(self) -> List[int]:
        return self.slots_used

    def final_as_row(self) -> Dict[str, Union[str, int]]:
        return {
            "steps": self.steps(),
            " top_of_stack": self.final_stack_top(),
            "max_stack_height": self.max_stack_height(),
            **self.final_scratch(with_formatting=True),
        }


def lightly_encode_output(out: Union[int, str], logs=False) -> str:
    """
    Encoding convention for Black Box Testing.

    * Assumes int's are uint64 and encodes them into hex str's
    *
    """
    _encoding_assertion(out)

    if isinstance(out, int):
        return out.to_bytes(8, "big").hex() if logs else out

    if isinstance(out, str):
        return bytes(out, "utf-8").hex()


def lightly_encode_args(args: List[Union[str, int]]) -> List[str]:
    """
    Encoding convention for Black Box Testing.

    * Assumes int's are uint64 and encodes them as such
    * Leaves str's alone
    """

    def encode(arg, idx):
        _encoding_assertion(arg, f"problem at args index {idx}")
        return (
            arg if isinstance(arg, str) else arg.to_bytes(8, byteorder="big")
        )

    return [encode(a, i) for i, a in enumerate(args)]


def _encoding_assertion(arg: Any, msg: str = "") -> None:
    assert isinstance(
        arg, (int, str)
    ), f"{msg +': ' if msg else ''}can't handle arg [{arg}] of type {type(arg)}"
    if isinstance(arg, int):
        assert arg >= 0, f"can't handle negative arguments but was given {arg}"


def make_table(
    black_box_result: BlackBoxResults,
    col_max: int,
    scratch_verbose: bool = False,
    scratch_before_stack: bool = True,
):
    assert not (
        scratch_verbose and scratch_before_stack
    ), "Cannot request scratch columns before stack when verbose"

    def empty_hack(se):
        return se if se else [""]

    rows = [
        list(
            map(
                str,
                [
                    i + 1,
                    black_box_result.program_counters[i],
                    black_box_result.teal_line_numbers[i],
                    black_box_result.teal_source_lines[i],
                    black_box_result.stack_evolution[i],
                    *empty_hack(black_box_result.scratch_evolution[i]),
                ],
            )
        )
        for i in range(black_box_result.steps_executed)
    ]
    if col_max and col_max > 0:
        rows = [[x[:col_max] for x in row] for row in rows]
    headers = [
        "step",
        "PC#",
        "L#",
        "Teal",
        "Stack",
        *(
            [f"S@{s}" for s in black_box_result.slots_used]
            if scratch_verbose
            else ["Scratch"]
        ),
    ]
    if scratch_before_stack:
        # with assertion above, we know that there is only one
        # scratch column and it's at the very end
        headers[-1], headers[-2] = headers[-2], headers[-1]
        for i in range(len(rows)):
            rows[i][-1], rows[i][-2] = rows[i][-2], rows[i][-1]

    table = tabulate(rows, headers=headers, tablefmt="presto")
    return table


def scrape_the_black_box(
    trace, lines, scratch_colon: str = "->", scratch_verbose: bool = False
) -> BlackBoxResults:
    pcs = [t["pc"] for t in trace]
    line_nums = [t["line"] for t in trace]

    def line_or_err(i, ln):
        line = lines[ln - 1]
        err = trace[i].get("error")
        return err if err else line

    tls = [line_or_err(i, ln) for i, ln in enumerate(line_nums)]
    N = len(pcs)
    assert N == len(
        tls
    ), f"mismatch of lengths in pcs v. tls ({N} v. {len(tls)})"

    # process stack var's
    raw_stacks = [
        [TealVal.from_stack(s) for s in x] for x in [t["stack"] for t in trace]
    ]
    stacks = [f"[{', '.join(map(str,stack))}]" for stack in raw_stacks]
    assert N == len(
        stacks
    ), f"mismatch of lengths in tls v. stacks ({N} v. {len(stacks)})"

    # process scratch var's
    scratches = [
        [TealVal.from_scratch(s) for s in x]
        for x in [t.get("scratch", []) for t in trace]
    ]
    scratches = [
        {i: s for i, s in enumerate(scratch) if not s.is_empty()}
        for scratch in scratches
    ]
    slots_used = sorted(set().union(*(s.keys() for s in scratches)))
    final_scratch_state = scratches[-1]
    if not scratch_verbose:

        def compute_delta(prev, curr):
            pks, cks = set(prev.keys()), set(curr.keys())
            new_keys = cks - pks
            if new_keys:
                return {k: curr[k] for k in new_keys}
            return {k: v for k, v in curr.items() if prev[k] != v}

        scratch_deltas = [scratches[0]]
        for i in range(1, len(scratches)):
            scratch_deltas.append(
                compute_delta(scratches[i - 1], scratches[i])
            )

        scratches = [
            [f"{i}{scratch_colon}{v}" for i, v in scratch.items()]
            for scratch in scratch_deltas
        ]
    else:
        scratches = [
            [
                f"{i}{scratch_colon}{scratch[i]}" if i in scratch else ""
                for i in slots_used
            ]
            for scratch in scratches
        ]

    assert N == len(
        scratches
    ), f"mismatch of lengths in tls v. scratches ({N} v. {len(scratches)})"

    bbr = BlackBoxResults(
        N,
        pcs,
        line_nums,
        tls,
        stacks,
        scratches,
        final_scratch_state,
        slots_used,
        raw_stacks,
    )
    bbr.assert_well_defined()
    return bbr


def get_blackbox_scenario_components(
    scenario: Dict[str, Union[list, dict]], mode: Mode
) -> Tuple[List[tuple], Dict[DRA, Any]]:
    assert isinstance(
        scenario, dict
    ), f"a Blackbox Scenario should be a dict but got a {type(scenario)}"

    inputs = scenario.get("inputs")
    assert (
        inputs
        and isinstance(inputs, list)
        and all(isinstance(args, tuple) for args in inputs)
    ), "need a list of inputs with at least one args and all args must be tuples"

    assertions = scenario.get("assertions", {})
    if assertions:
        assert isinstance(assertions, dict), f"assertions must be a dict"

        for key in assertions:
            assert isinstance(key, DRA) and mode_has_assertion(
                mode, key
            ), "each key must be a DryrunAssertionTypes appropriate to {mode}. This is not the case for key {key}"

    return inputs, assertions


class SequenceAssertion:
    def __init__(
        self,
        predicate: Union[Dict[Tuple, Union[str, int]], Callable],
        enforce: bool = False,
        name: str = None,
    ):
        self.definition = predicate
        self.predicate, self._expected = self.prepare_predicate(predicate)
        self.enforce = enforce
        self.name = name

    def __repr__(self):
        return f"SequenceAssertion({self.definition})"[:100]

    def __call__(
        self, args: list, actual: Union[str, int]
    ) -> Tuple[bool, str]:
        assertion = self.predicate(args, actual)
        msg = ""
        if not assertion:
            msg = f"SequenceAssertion for '{self.name}' failed for for args {args}: actual is [{actual}] BUT expected [{self.expected(args)}]"
            if self.enforce:
                assert assertion, msg

        return assertion, msg

    def expected(self, args: list) -> Union[str, int]:
        return self._expected(args)

    @classmethod
    def prepare_predicate(cls, predicate):
        if isinstance(predicate, dict):
            return (
                lambda args, actual: predicate[args] == actual,
                lambda args: predicate[args],
            )

        if not isinstance(predicate, Callable):
            # constant function in this case:
            return lambda _, actual: predicate == actual, lambda _: predicate

        try:
            sig = signature(predicate)
        except Exception as e:
            raise Exception(
                f"callable predicate {predicate} must have a signature"
            ) from e

        N = len(sig.parameters)
        assert N in (1, 2), f"predicate has the wrong number of paramters {N}"

        if N == 2:
            return predicate, lambda _: predicate

        # N == 1:
        return lambda args, actual: predicate(
            args
        ) == actual, lambda args: predicate(args)


def mode_has_assertion(
    mode: Mode, assertion_type: DryRunAssertionType
) -> bool:
    missing = {
        Mode.Signature: {
            DryRunAssertionType.cost,
            DryRunAssertionType.lastLog,
        },
        Mode.Application: set(),
    }
    if assertion_type in missing[mode]:
        return False

    return True


def dig_actual(
    dryrun_resp: dict,
    assert_type: DryRunAssertionType,
    assertion_arg: Any = None,
) -> Union[str, int, bool]:
    txns = dryrun_resp["txns"]
    assert (
        len(txns) == 1
    ), f"expecting exactly 1 transaction but got {len(txns)}"
    txn = txns[0]
    mode = Mode.Signature if "logic-sig-messages" in txn else Mode.Application
    is_app = mode == Mode.Application

    assert mode_has_assertion(
        mode, assert_type
    ), f"{mode} cannot handle dig information from txn for assertion type {assert_type}"
    is_app = mode == Mode.Application

    if assert_type == DryRunAssertionType.cost:
        return txn["cost"]

    if assert_type == DryRunAssertionType.lastLog:
        last_log = txn.get("logs", [None])[-1]
        if last_log is None:
            return last_log
        return b64decode(last_log).hex()

    if assert_type == DryRunAssertionType.finalScratch:
        trace = extract_trace(txn, is_app)
        lines = extract_lines(txn, is_app)
        bbr = scrape_the_black_box(trace, lines)
        return {
            k: v.as_python_type() for k, v in bbr.final_scratch_state.items()
        }

    if assert_type == DryRunAssertionType.stackTop:
        trace = extract_trace(txn, is_app)
        stack = trace[-1]["stack"]
        if not stack:
            return None
        tv = TealVal.from_scratch(stack[-1])
        return tv.as_python_type()

    if assert_type == DryRunAssertionType.maxStackHeight:
        return max(len(t["stack"]) for t in extract_trace(txn, is_app))

    if assert_type == DryRunAssertionType.status:
        return extract_status(mode, txn)

    if assert_type == DryRunAssertionType.passed:
        return extract_status(mode, txn) == "PASS"

    if assert_type == DryRunAssertionType.rejected:
        return extract_status(mode, txn) == "REJECT"

    if assert_type == DryRunAssertionType.error:
        ok, msg = assert_error(
            dryrun_resp, pattern=assertion_arg, enforce=False
        )
        return ok or msg

    if assert_type == DryRunAssertionType.noError:
        ok, msg = assert_no_error(dryrun_resp, enforce=False)
        return ok or msg

    raise Exception(f"Unknown assert_type {assert_type}")


def extract_logs(txn, decode_logs: bool = True):
    return [b64decode(log).hex() for log in txn.get("logs", [])]


def extract_cost(txn):
    return txn.get("cost")


def extract_status(mode, txn):
    return (
        txn["logic-sig-messages"][-1]
        if mode == Mode.Signature
        else txn["app-call-messages"][-1]
    )


def extract_lines(txn, is_app):
    return txn["disassembly" if is_app else "logic-sig-disassembly"]


def extract_trace(txn, is_app):
    return txn["app-call-trace" if is_app else "logic-sig-trace"]


def extract_messages(txn, is_app):
    return txn["app-call-messages" if is_app else "logic-sig-messages"]


def extract_local_deltas(txn):
    return txn.get("local-deltas", [])


def extract_global_delta(txn):
    return txn.get("global-delta", [])


def extract_all(txn: dict, is_app: bool, decode_logs: bool = True) -> dict:
    trace = extract_trace(txn, is_app)
    lines = extract_lines(txn, is_app)
    bbr = scrape_the_black_box(trace, lines)

    return {
        "cost": extract_cost(txn),
        "logs": extract_logs(txn, decode_logs=decode_logs),
        "gdelta": extract_global_delta(txn),
        "ldeltas": extract_local_deltas(txn),
        "messages": extract_messages(txn, is_app),
        "trace": trace,
        "lines": lines,
        "bbr": bbr,
    }


def dryrun_report_row(
    row_num: int, args: List[Union[int, str]], txn: dict, is_app: bool
) -> dict:
    extracts = extract_all(txn, is_app)
    logs = extracts["logs"]
    return {
        " Run": row_num,
        " cost": extracts["cost"],
        # back-tick needed to keep Excel/Google sheets from stumbling over hex
        " final_log": f"`{logs[-1]}" if logs else None,
        " final_message": extracts["messages"][-1],
        **extracts["bbr"].final_as_row(),
        **{f"Arg_{i:02}": arg for i, arg in enumerate(args)},
    }


def csv_from_dryrun_logicsigs(
    inputs: List[Tuple[Union[int, str]]], dr_resps: List[dict]
) -> str:
    return drresps_as_csv(inputs, dr_resps, False)


def csv_from_dryrun_apps(
    inputs: List[Tuple[Union[int, str]]], dr_resps: List[dict]
) -> str:
    return drresps_as_csv(inputs, dr_resps, True)


def drresps_as_csv(
    inputs: List[tuple], dr_resps: List[dict], is_app: bool
) -> str:
    N = len(inputs)
    assert N == len(
        dr_resps
    ), f"cannot produce CSV with unmatching size of inputs ({len(inputs)}) v. drresps ({len(dr_resps)})"

    txns = []
    for i, dr_resp in enumerate(dr_resps):
        _txns = dr_resp.get("txns", [])
        assert (
            len(_txns) == 1
        ), f"need exactly one txn per dr_resp but got {len(_txns)} at index {i}"

        txns.append(_txns[0])

    return txns_as_csv(inputs, txns, is_app)


def txns_as_csv(inputs: List[tuple], txns: List[dict], is_app: bool) -> str:
    N = len(inputs)
    assert N == len(
        txns
    ), f"cannot produce CSV with unmatching size of inputs ({len(inputs)}) v. txns ({len(txns)})"
    assert txns, "cannot produce CSV from an empty list"

    txns = [
        dryrun_report_row(i + 1, inputs[i], txn, is_app)
        for i, txn in enumerate(txns)
    ]
    with io.StringIO() as csv_str:
        fields = sorted(set().union(*(txn.keys() for txn in txns)))
        writer = csv.DictWriter(csv_str, fieldnames=fields)
        writer.writeheader()
        for txn in txns:
            writer.writerow(txn)

        return csv_str.getvalue()


def dryrun_assert(
    inputs: List[list],
    dryrun_resps: List[dict],
    assert_type: DryRunAssertionType,
    test: SequenceAssertion,
):
    N = len(inputs)
    assert N == len(
        dryrun_resps
    ), f"inputs (len={N}) and dryrun responses (len={len(dryrun_resps)}) must have the same length"

    assert isinstance(
        assert_type, DryRunAssertionType
    ), f"assertions types must be DryRunAssertionType's but got [{assert_type}] which is a {type(assert_type)}"

    for i, args in enumerate(inputs):
        resp = dryrun_resps[i]
        txns = resp["txns"]
        assert (
            len(txns) == 1
        ), f"expecting exactly 1 transaction but got {len(txns)}"
        txn = txns[0]
        mode = (
            Mode.Signature if "logic-sig-messages" in txn else Mode.Application
        )
        is_app = mode == Mode.Application

        actual = dig_actual(resp, assert_type)
        ok, msg = test(args, actual)
        if not ok:
            extracts = extract_all(txn, is_app)
            cost = extracts["cost"]
            logs = extracts["logs"]
            gdelta = extracts["gdelta"]
            ldelta = extracts["ldeltas"]
            messages = extracts["messages"]
            bbr = extracts["bbr"]
            table = make_table(bbr, -1)

            assert ok, f"""===============
<<<<<<<<<<<{msg}>>>>>>>>>>>>>
===============
App Trace:
{table}
===============
MODE: {mode}
TOTAL COST: {cost}
===============
txn.app_call_rejected={messages[-1] != 'PASS'}
===============
Messages: {messages}
Logs: {logs}
===============
-----{bbr}-----
TOTAL STEPS: {bbr.steps()}
FINAL STACK: {bbr.final_stack()}
FINAL STACK TOP: {bbr.final_stack_top()}
MAX STACK HEIGHT: {bbr.max_stack_height()}
FINAL SCRATCH: {bbr.final_scratch()}
SLOTS USED: {bbr.slots()}
FINAL AS ROW: {bbr.final_as_row()}
===============
Global Delta:
{gdelta}
===============
Local Delta:
{ldelta}
===============
TXN AS ROW: {dryrun_report_row(i+1, args, txn, is_app)}
===============
<<<<<<<<<<<{msg}>>>>>>>>>>>>>
===============
"""
