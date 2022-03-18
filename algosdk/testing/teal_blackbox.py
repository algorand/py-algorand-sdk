from base64 import b64decode
import csv
from dataclasses import dataclass
from enum import Enum
import io
from tabulate import tabulate
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

from algosdk.v2client.algod import AlgodClient
from algosdk.testing.dryrun import (
    ZERO_ADDRESS,
    assert_error,
    assert_no_error,
    Helper as DryRunHelper,
)

ExecutionMode = Enum("ExecutionMode", "Signature Application")

DryRunProperty = Enum(
    "DryRunProperty",
    "cost lastLog finalScratch stackTop maxStackHeight status rejected passed error noError globalStateHas localStateHas",
)
DRProp = DryRunProperty

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
        return f"0x{b64decode(self.b).hex()}" if self.is_b else str(self.i)

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


def dryrun_encode_out(out: Union[int, str], logs=False) -> str:
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


def dryrun_encode_args(args: Iterable[Union[str, int]]) -> List[str]:
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


def dryrun_encode_scratch(x) -> str:
    x = x.to_bytes(8, "big") if isinstance(x, int) else x.encode("utf-8")
    return f"0x{x.hex()}"


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
    scenario: Dict[str, Union[list, dict]], mode: ExecutionMode
) -> Tuple[List[tuple], Dict[DRProp, Any]]:
    """
    Validate that a Blackbox Test Scenario has been properly constructed, and return back
    its components which consist of **inputs** and _optional_ **assertions**.

    A scenario should adhere to the following schema:
    ```
    {
        "inputs":       List[Tuple[Union[str, int]]],
        "assertions":   Dict[DryRunAssertionType, ...an assertion...]
    }

    Each assertion is a map from _assertion type_  to be made on a dry run,
    to the actual assertion. Actual assertions can be:
    * simple python types - these are useful in the case of _constant_ assertions.
        For example, if you want to assert that the `maxStackHeight` is 3, just use `3`.
    * dictionaries of type Dict[Tuple, Any] - these are useful when you just want to assert
        a discrete set of input-output pairs.
        For example, if you have 4 inputs that you want to assert are being squared,
        you could use `{(2,): 4, (7,): 49, (13,): 169, (11,): 121}`
    * functions which take a single variable. These are useful when you have a python "simulator"
        for the assertions.
        In the square example you could use `lambda args: args[0]**2`
    * functions which take _two_ variables. These are useful when your assertion is more
        subtle that out-and-out equality. For example, suppose you want to assert that the
        `cost` of the dry run is `2*n` plus/minus 5 where `n` is the first arg of the input. Then
        you could use `lambda args, actual: 2*args[0] - 5 <= actual <= 2*args[0] + 5`
    ```
    """
    assert isinstance(
        scenario, dict
    ), f"a Blackbox Scenario should be a dict but got a {type(scenario)}"

    inputs = scenario.get("inputs")
    # TODO: we can be more flexible here and allow arbitrary iterable `args`. Because
    # assertions are allowed to be dicts, and therefore each `args` needs to be
    # hashable in that case, we are restricting to tuples currently.
    # However, this function could be friendlier and just _convert_ each of the
    # `args` to a tuple, thus eliminating any downstream issues.
    assert (
        inputs
        and isinstance(inputs, list)
        and all(isinstance(args, tuple) for args in inputs)
    ), "need a list of inputs with at least one args and all args must be tuples"

    assertions = scenario.get("assertions", {})
    if assertions:
        assert isinstance(assertions, dict), f"assertions must be a dict"

        for key in assertions:
            assert isinstance(key, DRProp) and mode_has_assertion(
                mode, key
            ), f"each key must be a DryrunAssertionTypes appropriate to {mode}. This is not the case for key {key}"

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
    mode: ExecutionMode, assertion_type: DryRunProperty
) -> bool:
    missing = {
        ExecutionMode.Signature: {
            DryRunProperty.cost,
            DryRunProperty.lastLog,
        },
        ExecutionMode.Application: set(),
    }
    if assertion_type in missing[mode]:
        return False

    return True


def _dig_impl(
    dryrun_resp: dict, property: DryRunProperty, **kwargs: Dict[str, Any]
) -> Union[str, int, bool]:
    txns = dryrun_resp["txns"]
    assert (
        len(txns) == 1
    ), f"expecting exactly 1 transaction but got {len(txns)}"
    txn = txns[0]
    mode = (
        ExecutionMode.Signature
        if "logic-sig-messages" in txn
        else ExecutionMode.Application
    )

    assert mode_has_assertion(
        mode, property
    ), f"{mode} cannot handle dig information from txn for assertion type {property}"
    is_app = mode == ExecutionMode.Application

    if property == DryRunProperty.cost:
        return txn["cost"]

    if property == DryRunProperty.lastLog:
        last_log = txn.get("logs", [None])[-1]
        if last_log is None:
            return last_log
        return b64decode(last_log).hex()

    if property == DryRunProperty.finalScratch:
        trace = extract_trace(txn, is_app)
        lines = extract_lines(txn, is_app)
        bbr = scrape_the_black_box(trace, lines)
        return {
            k: v.as_python_type() for k, v in bbr.final_scratch_state.items()
        }

    if property == DryRunProperty.stackTop:
        trace = extract_trace(txn, is_app)
        stack = trace[-1]["stack"]
        if not stack:
            return None
        tv = TealVal.from_scratch(stack[-1])
        return tv.as_python_type()

    if property == DryRunProperty.maxStackHeight:
        return max(len(t["stack"]) for t in extract_trace(txn, is_app))

    if property == DryRunProperty.status:
        return extract_status(mode, txn)

    if property == DryRunProperty.passed:
        return extract_status(mode, txn) == "PASS"

    if property == DryRunProperty.rejected:
        return extract_status(mode, txn) == "REJECT"

    if property == DryRunProperty.error:
        pattern = kwargs.get("pattern")
        ok, msg = assert_error(dryrun_resp, pattern=pattern, enforce=False)
        # when there WAS an error, we return its msg, else False
        return ok

    if property == DryRunProperty.noError:
        ok, msg = assert_no_error(dryrun_resp, enforce=False)
        # when there was NO error, we return True, else return its msg
        return ok or msg

    raise Exception(f"Unknown assert_type {property}")


def extract_logs(txn):
    return [b64decode(log).hex() for log in txn.get("logs", [])]


def extract_cost(txn):
    return txn.get("cost")


def extract_status(mode, txn):
    return (
        txn["logic-sig-messages"][0]
        if mode == ExecutionMode.Signature
        else txn["app-call-messages"][1]
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


def extract_all(txn: dict, is_app: bool) -> dict:
    trace = extract_trace(txn, is_app)
    lines = extract_lines(txn, is_app)
    bbr = scrape_the_black_box(trace, lines)

    return {
        "cost": extract_cost(txn),
        "logs": extract_logs(txn),
        "gdelta": extract_global_delta(txn),
        "ldeltas": extract_local_deltas(txn),
        "messages": extract_messages(txn, is_app),
        "trace": trace,
        "lines": lines,
        "bbr": bbr,
    }


def guess_txn_mode(txn: dict, enforce: bool = True) -> ExecutionMode:
    """
    Guess the mode based on location of traces. If no luck, raise an AssertionError
    (or just return None if not enforce)
    """
    akey, lskey = "app-call-trace", "logic-sig-trace"
    if akey in txn:
        return ExecutionMode.Application

    if lskey in txn:
        return ExecutionMode.Signature

    if enforce:
        raise AssertionError(
            f"transaction's Mode cannot be guessed as it doesn't contain any of {(akey, lskey)}"
        )

    return None


def _dryrun_report_row(
    row_num: int, args: List[Union[int, str]], txn: dict, is_app: bool = None
) -> dict:
    """
    when is_app is not supplied, attempt to auto-detect whether dry run is a logic sig or an app
    """
    if is_app is None:
        is_app = guess_txn_mode(txn) == ExecutionMode.Application

    extracts = extract_all(txn, is_app)
    logs = extracts["logs"]
    return {
        " Run": row_num,
        " cost": extracts["cost"],
        # back-tick needed to keep Excel/Google sheets from stumbling over hex
        " final_log": f"`{logs[-1]}" if logs else None,
        " final_message": extracts["messages"][-1],
        " Status": extracts["messages"][1 if is_app else 0],
        **extracts["bbr"].final_as_row(),
        **{f"Arg_{i:02}": arg for i, arg in enumerate(args)},
    }


def csv_from_dryruns(inputs: List[tuple], dr_resps: List[dict]) -> str:
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

    return _txns_as_csv(inputs, txns)


def _txns_as_csv(inputs: List[tuple], txns: List[dict]) -> str:
    N = len(inputs)
    assert N == len(
        txns
    ), f"cannot produce CSV with unmatching size of inputs ({len(inputs)}) v. txns ({len(txns)})"
    assert txns, "cannot produce CSV from an empty list"

    txns = [
        _dryrun_report_row(i + 1, inputs[i], txn) for i, txn in enumerate(txns)
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
    assert_type: DryRunProperty,
    test: SequenceAssertion,
):
    N = len(inputs)
    assert N == len(
        dryrun_resps
    ), f"inputs (len={N}) and dryrun responses (len={len(dryrun_resps)}) must have the same length"

    assert isinstance(
        assert_type, DryRunProperty
    ), f"assertions types must be DryRunAssertionType's but got [{assert_type}] which is a {type(assert_type)}"

    for i, args in enumerate(inputs):
        resp = dryrun_resps[i]
        txns = resp["txns"]
        assert (
            len(txns) == 1
        ), f"expecting exactly 1 transaction but got {len(txns)} for dryrun_resps[{i}]"
        txn = txns[0]
        mode = (
            ExecutionMode.Signature
            if "logic-sig-messages" in txn
            else ExecutionMode.Application
        )
        is_app = mode == ExecutionMode.Application

        actual = _dig_impl(resp, assert_type)
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
FINAL MESSAGE: {messages[-1]}
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
TXN AS ROW: {_dryrun_report_row(i+1, args, txn, is_app)}
===============
<<<<<<<<<<<{msg}>>>>>>>>>>>>>
===============
"""


def execute_singleton_app(
    algod: AlgodClient,
    teal: str,
    args: Iterable[Union[str, int]],
    sender: str = ZERO_ADDRESS,
) -> "DryRunTransactionResult":
    return execute_singleton_dryrun(
        algod, teal, args, ExecutionMode.Application, sender=sender
    )


def execute_singleton_logicsig(
    algod: AlgodClient,
    teal: str,
    args: Iterable[Union[str, int]],
    sender: str = ZERO_ADDRESS,
) -> "DryRunTransactionResult":
    return execute_singleton_dryrun(
        algod, teal, args, ExecutionMode.Signature, sender
    )


def execute_singleton_dryrun(
    algod: AlgodClient,
    teal: str,
    args: Iterable[Union[str, int]],
    mode: ExecutionMode,
    sender: str = ZERO_ADDRESS,
) -> "DryRunTransactionResult":
    assert (
        len(ExecutionMode) == 2
    ), f"assuming only 2 ExecutionMode's but have {len(ExecutionMode)}"
    assert mode in ExecutionMode, f"unknown mode {mode} of type {type(mode)}"
    is_app = mode == ExecutionMode.Application

    args = dryrun_encode_args(args)
    builder = (
        DryRunHelper.singleton_app_request
        if is_app
        else DryRunHelper.singleton_logicsig_request
    )
    dryrun_req = builder(teal, args, sender=sender)
    dryrun_resp = algod.dryrun(dryrun_req)
    return DryRunTransactionResult.singleton(dryrun_resp)


class DryRunTransactionResult:
    """
    TODO: merge this with @barnjamin's class of PR #283
    """

    def __init__(self, dryrun_resp: dict, txn_index: int):
        txns = dryrun_resp.get("txns", [])
        assert txns, "Dry Run response is missing transactions"

        assert (
            0 <= txn_index < len(txns)
        ), f"Out of bounds txn_index {txn_index} when there are only {len(txns)} transactions in the Dry Run response"

        txn = txns[txn_index]

        self.mode: ExecutionMode = self.get_txn_mode(txn)
        self.parent_dryrun_response: dict = dryrun_resp
        self.txn: dict = txn

    @classmethod
    def get_txn_mode(cls, txn: dict) -> ExecutionMode:
        """
        Guess the mode based on location of traces. If no luck, raise an AssertionError
        """
        keyset = set(txn.keys())
        akey, lskey = "app-call-trace", "logic-sig-trace"
        assert (
            len({akey, lskey} & keyset) == 1
        ), f"ambiguous mode for dry run transaction: expected exactly one of '{akey}', '{lskey}' to be in keyset {keyset}"

        if akey in keyset:
            return ExecutionMode.Application

        return ExecutionMode.Signature

    @classmethod
    def singleton(cls, dryrun_resp: dict) -> "DryRunTransactionResult":
        txns = dryrun_resp.get("txns") or []
        assert (
            len(txns) == 1
        ), f"require exactly 1 dry run transaction to create a singleton but had {len(txns)} instead"

        return cls(dryrun_resp, 0)

    def dig(self, property: DryRunProperty, **kwargs: Dict[str, Any]) -> Any:
        return _dig_impl(self.parent_dryrun_response, property, **kwargs)

    def cost(self) -> int:
        return self.dig(DRProp.cost)

    def last_log(self) -> str:
        return self.dig(DRProp.lastLog)

    def final_scratch(self) -> Dict[int, Union[int, str]]:
        return self.dig(DRProp.finalScratch)

    def max_stack_height(self) -> int:
        return self.dig(DRProp.maxStackHeight)

    def stack_top(self) -> int:
        return self.dig(DRProp.stackTop)

    def status(self) -> str:
        return self.dig(DRProp.status)

    def passed(self) -> bool:
        return self.dig(DRProp.passed)

    def rejected(self) -> bool:
        return self.dig(DRProp.rejected)

    def error(self, pattern=None) -> bool:
        return self.dig(DRProp.error, pattern=pattern)

    def noError(self) -> Union[bool, str]:
        """
        Returns error message in the case there was actualluy an erorr
        """
        return self.dig(DRProp.noError)
