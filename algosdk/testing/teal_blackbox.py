from base64 import b64decode
import csv
from dataclasses import dataclass
from enum import Enum, auto
import io
from inspect import signature
from tabulate import tabulate
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from algosdk.v2client.algod import AlgodClient
from algosdk.testing.dryrun import (
    ZERO_ADDRESS,
    assert_error,
    assert_no_error,
    Helper as DryRunHelper,
)


class ExecutionMode(Enum):
    Signature = auto()
    Application = auto()


class DryRunProperty(Enum):
    cost = auto()
    lastLog = auto()
    finalScratch = auto()
    stackTop = auto()
    maxStackHeight = auto()
    status = auto()
    rejected = auto()
    passed = auto()
    error = auto()
    errorMessage = auto()
    globalStateHas = auto()
    localStateHas = auto()


DRProp = DryRunProperty


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

    @classmethod
    def scrape(
        cls,
        trace,
        lines,
        scratch_colon: str = "->",
        scratch_verbose: bool = False,
    ) -> "BlackBoxResults":
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
            [TealVal.from_stack(s) for s in x]
            for x in [t["stack"] for t in trace]
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

        bbr = cls(
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


class DryRunEncoder:
    """Encoding utilities for dry run executions and results"""

    @classmethod
    def encode_args(cls, args: Iterable[Union[str, int]]) -> List[str]:
        """
        Encoding convention for Black Box Testing.

        * Assumes int's are uint64 and encodes them as such
        * Leaves str's alone
        """
        return [cls._encode_arg(a, i) for i, a in enumerate(args)]

    @classmethod
    def hex0x(cls, x) -> str:
        return f"0x{cls.hex(x)}"

    @classmethod
    def hex(cls, out: Union[int, str]) -> str:
        """
        Encoding convention for Black Box Testing.

        * Assumes int's are uint64
        * Assumes everything else is a str
        * Encodes them into hex str's
        """
        cls._assert_encodable(out)
        return cls._to_bytes(out).hex()

    @classmethod
    def _to_bytes(cls, x, only_ints=False):
        is_int = isinstance(x, int)
        if only_ints and not is_int:
            return x
        return x.to_bytes(8, "big") if is_int else bytes(x, "utf-8")

    @classmethod
    def _encode_arg(cls, arg, idx):
        cls._assert_encodable(
            arg, f"problem encoding arg ({arg}) at index ({idx})"
        )
        return cls._to_bytes(arg, only_ints=True)

    @classmethod
    def _assert_encodable(cls, arg: Any, msg: str = "") -> None:
        assert isinstance(
            arg, (int, str)
        ), f"{msg +': ' if msg else ''}can't handle arg [{arg}] of type {type(arg)}"
        if isinstance(arg, int):
            assert (
                arg >= 0
            ), f"can't handle negative arguments but was given {arg}"


class DryRunExecutor:
    """Methods to package up and kick off dry run executions"""

    @classmethod
    def dryrun_app(
        cls,
        algod: AlgodClient,
        teal: str,
        args: Iterable[Union[str, int]],
        sender: str = ZERO_ADDRESS,
    ) -> "DryRunTransactionResult":
        return cls.execute_one_dryrun(
            algod, teal, args, ExecutionMode.Application, sender=sender
        )

    @classmethod
    def dryrun_logicsig(
        cls,
        algod: AlgodClient,
        teal: str,
        args: Iterable[Union[str, int]],
        sender: str = ZERO_ADDRESS,
    ) -> "DryRunTransactionResult":
        return cls.execute_one_dryrun(
            algod, teal, args, ExecutionMode.Signature, sender
        )

    @classmethod
    def dryrun_app_on_sequence(
        cls,
        algod: AlgodClient,
        teal: str,
        inputs: List[Iterable[Union[str, int]]],
        sender: str = ZERO_ADDRESS,
    ) -> List["DryRunTransactionResult"]:
        return cls._map(cls.dryrun_app, algod, teal, inputs, sender)

    @classmethod
    def dryrun_logicsig_on_sequence(
        cls,
        algod: AlgodClient,
        teal: str,
        inputs: List[Iterable[Union[str, int]]],
        sender: str = ZERO_ADDRESS,
    ) -> List["DryRunTransactionResult"]:
        return cls._map(cls.dryrun_logicsig, algod, teal, inputs, sender)

    @classmethod
    def _map(cls, f, algod, teal, inps, sndr):
        return list(map(lambda args: f(algod, teal, args, sender=sndr), inps))

    @classmethod
    def execute_one_dryrun(
        cls,
        algod: AlgodClient,
        teal: str,
        args: Iterable[Union[str, int]],
        mode: ExecutionMode,
        sender: str = ZERO_ADDRESS,
    ) -> "DryRunTransactionResult":
        assert (
            len(ExecutionMode) == 2
        ), f"assuming only 2 ExecutionMode's but have {len(ExecutionMode)}"
        assert (
            mode in ExecutionMode
        ), f"unknown mode {mode} of type {type(mode)}"
        is_app = mode == ExecutionMode.Application

        args = DryRunEncoder.encode_args(args)
        builder = (
            DryRunHelper.singleton_app_request
            if is_app
            else DryRunHelper.singleton_logicsig_request
        )
        dryrun_req = builder(teal, args, sender=sender)
        dryrun_resp = algod.dryrun(dryrun_req)
        return DryRunTransactionResult.from_single_response(dryrun_resp)


class DryRunTransactionResult:
    """Methods to extract information from a single dry run transaction.
    TODO: merge this with @barnjamin's similarly named class of PR #283

    The class contains convenience methods and properties for inspecting
    dry run execution results on a _single transaction_ and for making
    assertions in tests.

    For example, let's execute a dry run for a logic sig teal program that purportedly computes $`x^2`$
    (see [lsig_square.teal](../../x/blackbox/teal/lsig_square.teal) for one such example).
    So assume you have a string `teal` containing that TEAL source and run the following:

    ```python
    >>> algod = get_algod()
    >>> x = 9
    >>> args = (x,)
    >>> dryrun_result = DryRunExecutor.dryrun_logicsig(algod, teal, args)
    >>> assert dryrun_result.status() == "PASS"
    >>> assert dryrun_result.stack_stop() == x ** 2
    ```
    In the above we have asserted the the program has succesfully exited with
    status "PASS" and that the top of the stack contained $`x^2 = 9`$.
    The _assertable properties_ were `status()` and `stack_top()`.

    DryRunTransactionResult provides the following **assertable properties**:
    * `cost`
        - total opcode cost utilized during execution
        - only available for apps
    * `last_log`
        - the final hex bytes that was logged during execution (apps only)
        - only available for apps
    * `logs`
        - similar to `last_log` but a list of _all_ the printed logs
    * `final_scratch`
        - the final scratch slot state contents represented as a dictionary
        - CAVEAT: slots containing a type's zero-value (0 or "") are not reported
    * `max_stack_height`
        - the maximum height of stack had during execution
    * `stack_top`
        - the contents of the top of the stack and the end of execution
    * `status`
        - either "PASS" when the execution succeeded or "REJECT" otherwise
    * `passed`
        - shorthand for `status() == "PASS"`
    * `rejected`
        - shorthand for `status() == "REJECT"`
    * `error` with optional `contains` matching
        - when no contains is provided, returns True exactly when execution fails due to error
        - when contains given, only return True if an error occured included contains
    * `noError`
        - returns True if there was no error, or the actual error when an error occured
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
        self.extracts: dict = self.extract_all(self.txn, self.is_app())
        self.black_box_results: BlackBoxResults = self.extracts["bbr"]

    def is_app(self) -> bool:
        return self.mode == ExecutionMode.Application

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
    def from_single_response(
        cls, dryrun_resp: dict
    ) -> "DryRunTransactionResult":
        txns = dryrun_resp.get("txns") or []
        assert (
            len(txns) == 1
        ), f"require exactly 1 dry run transaction to create a singleton but had {len(txns)} instead"

        return cls(dryrun_resp, 0)

    def dig(self, property: DryRunProperty, **kwargs: Dict[str, Any]) -> Any:
        """Main router for assertable properties"""
        txn = self.txn
        bbr = self.black_box_results

        assert SequenceAssertion.mode_has_assertion(
            self.mode, property
        ), f"{self.mode} cannot handle dig information from txn for assertion type {property}"

        if property == DryRunProperty.cost:
            return txn["cost"]

        if property == DryRunProperty.lastLog:
            last_log = txn.get("logs", [None])[-1]
            if last_log is None:
                return last_log
            return b64decode(last_log).hex()

        if property == DryRunProperty.finalScratch:
            return {
                k: v.as_python_type()
                for k, v in bbr.final_scratch_state.items()
            }

        if property == DryRunProperty.stackTop:
            trace = self.extracts["trace"]
            stack = trace[-1]["stack"]
            if not stack:
                return None
            tv = TealVal.from_scratch(stack[-1])
            return tv.as_python_type()

        if property == DryRunProperty.maxStackHeight:
            return max(len(t["stack"]) for t in self.extracts["trace"])

        if property == DryRunProperty.status:
            return self.extracts["status"]

        if property == DryRunProperty.passed:
            return self.extracts["status"] == "PASS"

        if property == DryRunProperty.rejected:
            return self.extracts["status"] == "REJECT"

        if property == DryRunProperty.error:
            contains = kwargs.get("contains")
            ok, msg = assert_error(
                self.parent_dryrun_response, contains=contains, enforce=False
            )
            # when there WAS an error, we return its msg, else False
            return ok

        if property == DryRunProperty.errorMessage:
            _, msg = assert_no_error(
                self.parent_dryrun_response, enforce=False
            )
            # when there was no error, we return None, else return its msg
            return msg if msg else None

        raise Exception(f"Unknown assert_type {property}")

    def cost(self) -> Optional[int]:
        """Assertable property for the total opcode cost that was used during dry run execution
        return type: int
        available Mode: Application only
        """
        return self.dig(DRProp.cost) if self.is_app() else None

    def last_log(self) -> Optional[str]:
        """Assertable property for the last log that was printed during dry run execution
        return type: string representing the hex bytes of the final log
        available Mode: Application only
        """
        return self.dig(DRProp.lastLog) if self.is_app() else None

    def logs(self) -> Optional[List[str]]:
        """Assertable property for all the logs that were printed during dry run execution
        return type: list of strings representing hex bytes of the logs
        available Mode: Application only
        """
        return self.extracts["logs"]

    def final_scratch(self) -> Dict[int, Union[int, str]]:
        """Assertable property for the scratch slots and their contents at the end of dry run execution
        return type: dictionary from strings to int's or strings
        available: all modes
        CAVEAT: slots containing a type's zero-value (0 or "") are not reported
        """
        return self.dig(DRProp.finalScratch)

    def max_stack_height(self) -> int:
        """Assertable property for the maximum height the stack had during a dry run execution
        return type: int
        available: all modes
        """
        return self.dig(DRProp.maxStackHeight)

    def stack_top(self) -> Union[int, str]:
        """Assertable property for the contents of the top of the stack and the end of a dry run execution
        return type: int or string
        available: all modes
        """
        return self.dig(DRProp.stackTop)

    def status(self) -> str:
        """Assertable property for the program run status at the end of dry run execution
        return type: string (either "PASS" or "REJECT")
        available: all modes
        """
        return self.dig(DRProp.status)

    def passed(self) -> bool:
        """Assertable property for the program's dry run execution having SUCCEEDED
        return type: bool
        available: all modes
        """
        return self.dig(DRProp.passed)

    def rejected(self) -> bool:
        """Assertable property for the program's dry run execution having FAILED
        return type: bool
        available: all modes
        """
        return self.dig(DRProp.rejected)

    def error(self, contains=None) -> bool:
        """Assertable property for a program having failed during dry run execution due to an error.
        The optional `contains` parameter allows specifying a particular string
        expected to be a _substring_ of the error's message. In case the program errors, but
        the contains did not match the actual error, False is returned.
            return type: bool
            available: all modes
        """
        return self.dig(DRProp.error, contains=contains)

    def error_message(self) -> Union[bool, str]:
        """Assertable property for a program having NOT failed and when failing, producing the failure message.
        return type: None (in the case of no error) or string with the error message, in case of error
        available: all modes
        """
        return self.dig(DRProp.errorMessage)

    def messages(self) -> List[str]:
        return self.extracts["messages"]

    def last_message(self) -> Optional[str]:
        return self.messages()[-1] if self.messages() else None

    def local_deltas(self) -> dict:
        return self.extracts["ldeltas"]

    def global_delta(self) -> dict:
        return self.extracts["gdelta"]

    def tabulate(
        self,
        col_max: int,
        scratch_verbose: bool = False,
        scratch_before_stack: bool = True,
    ):
        """Produce a string that when printed shows the evolution of a dry run.

        This is similar to DryrunTestCaseMixin's `pprint()` but also includes scratch
        variable evolution.

        For example, calling `tabulate()` with default values produces something like:

           step |   PC# |   L# | Teal                   | Scratch   | Stack
        --------+-------+------+------------------------+-----------+----------------------
              1 |     1 |    1 | #pragma version 6      |           | []
              2 |     4 |    2 | txna ApplicationArgs 0 |           | [0x0000000000000002]
              3 |     5 |    3 | btoi                   |           | [2]
              4 |    17 |   11 | label1:                |           | [2]
              5 |    19 |   12 | store 0                | 0->2      | []
              6 |    21 |   13 | load 0                 |           | [2]
              7 |    23 |   14 | pushint 2              |           | [2, 2]
              8 |    24 |   15 | exp                    |           | [4]
              9 |     8 |    4 | callsub label1         |           | [4]
             10 |    10 |    5 | store 1                | 1->4      | []
             11 |    12 |    6 | load 1                 |           | [4]
             12 |    13 |    7 | itob                   |           | [0x0000000000000004]
             13 |    14 |    8 | log                    |           | []
             14 |    16 |    9 | load 1                 |           | [4]
             15 |    25 |   16 | retsub                 |           | [4]
        """
        assert not (
            scratch_verbose and scratch_before_stack
        ), "Cannot request scratch columns before stack when verbose"
        bbr = self.black_box_results

        def empty_hack(se):
            return se if se else [""]

        rows = [
            list(
                map(
                    str,
                    [
                        i + 1,
                        bbr.program_counters[i],
                        bbr.teal_line_numbers[i],
                        bbr.teal_source_lines[i],
                        bbr.stack_evolution[i],
                        *empty_hack(bbr.scratch_evolution[i]),
                    ],
                )
            )
            for i in range(bbr.steps_executed)
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
                [f"S@{s}" for s in bbr.slots_used]
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

    def report(
        self, args: Iterable[Union[str, int]], msg: str, row: int = 0
    ) -> str:
        bbr = self.black_box_results
        return f"""===============
    <<<<<<<<<<<{msg}>>>>>>>>>>>>>
    ===============
    App Trace:
    {self.tabulate(-1)}
    ===============
    MODE: {self.mode}
    TOTAL COST: {self.cost()}
    ===============
    FINAL MESSAGE: {self.last_message()}
    ===============
    Messages: {self.messages()}
    Logs: {self.logs()}
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
    {self.global_delta()}
    ===============
    Local Delta:
    {self.local_deltas()}
    ===============
    TXN AS ROW: {self.csv_row(row, args)}
    ===============
    <<<<<<<<<<<{msg}>>>>>>>>>>>>>
    ===============
    """

    def csv_row(
        self, row_num: int, args: Iterable[Union[int, str]]
    ) -> Dict[str, Union[str, int]]:
        return {
            " Run": row_num,
            " cost": self.cost(),
            # back-tick needed to keep Excel/Google sheets from stumbling over hex
            " last_log": f"`{self.last_log()}",
            " final_message": self.last_message(),
            " Status": self.status(),
            **self.black_box_results.final_as_row(),
            **{f"Arg_{i:02}": arg for i, arg in enumerate(args)},
        }

    @classmethod
    def csv_report(
        cls, inputs: List[tuple], dr_resps: List["DryRunTransactionResult"]
    ) -> str:
        """Produce a Comma Separated Values report string capturing important statistics
        for a sequence of dry runs.

        For example, assuming you have a string `teal` which is a TEAL program computing $`x^2`$
        such as this [example program](x/blackbox/teal/app_square.teal).
        Let's run some Exploratory Dry Run Analysis (EDRA) for $`x`$ in the range $`[0, 10]`$:

        ```python
        >>> algod = get_algod()
        >>> inputs = [(x,) for x in range(11)]  # [(0), (1), ... , (10)]
        >>> dryrun_results = DryRunExecutor.dryrun_app_on_sequence(algod, teal, inputs)
        >>> csv = DryRunTransactionResult.csv_report(inputs, dryrun_results)
        >>> print(csv)
        ```
        Then you would get the following output:
        ```plain
         Run, Status, cost, final_message, last_log, top_of_stack,Arg_00,max_stack_height,s@000,s@001,steps
        1,REJECT,14,REJECT,`None,0,0,2,,,15
        2,PASS,14,PASS,`0000000000000001,1,1,2,1,1,15
        3,PASS,14,PASS,`0000000000000004,4,2,2,2,4,15
        4,PASS,14,PASS,`0000000000000009,9,3,2,3,9,15
        5,PASS,14,PASS,`0000000000000010,16,4,2,4,16,15
        6,PASS,14,PASS,`0000000000000019,25,5,2,5,25,15
        7,PASS,14,PASS,`0000000000000024,36,6,2,6,36,15
        8,PASS,14,PASS,`0000000000000031,49,7,2,7,49,15
        9,PASS,14,PASS,`0000000000000040,64,8,2,8,64,15
        10,PASS,14,PASS,`0000000000000051,81,9,2,9,81,15
        ```
        """
        N = len(inputs)
        assert N == len(
            dr_resps
        ), f"cannot produce CSV with unmatching size of inputs ({len(inputs)}) v. drresps ({len(dr_resps)})"

        dr_resps = [
            resp.csv_row(i + 1, inputs[i]) for i, resp in enumerate(dr_resps)
        ]
        with io.StringIO() as csv_str:
            fields = sorted(set().union(*(txn.keys() for txn in dr_resps)))
            writer = csv.DictWriter(csv_str, fieldnames=fields)
            writer.writeheader()
            for txn in dr_resps:
                writer.writerow(txn)

            return csv_str.getvalue()

    @classmethod
    def extract_logs(cls, txn):
        return [b64decode(log).hex() for log in txn.get("logs", [])]

    @classmethod
    def extract_cost(cls, txn):
        return txn.get("cost")

    @classmethod
    def extract_status(cls, txn, is_app: bool):
        key, idx = (
            ("app-call-messages", 1) if is_app else ("logic-sig-messages", 0)
        )
        return txn[key][idx]

    @classmethod
    def extract_messages(cls, txn, is_app):
        return txn["app-call-messages" if is_app else "logic-sig-messages"]

    @classmethod
    def extract_local_deltas(cls, txn):
        return txn.get("local-deltas", [])

    @classmethod
    def extract_global_delta(cls, txn):
        return txn.get("global-delta", [])

    @classmethod
    def extract_lines(cls, txn, is_app):
        return txn["disassembly" if is_app else "logic-sig-disassembly"]

    @classmethod
    def extract_trace(cls, txn, is_app):
        return txn["app-call-trace" if is_app else "logic-sig-trace"]

    @classmethod
    def extract_all(cls, txn: dict, is_app: bool) -> dict:
        result = {
            "logs": cls.extract_logs(txn),
            "cost": cls.extract_cost(txn),
            "status": cls.extract_status(txn, is_app),
            "messages": cls.extract_messages(txn, is_app),
            "ldeltas": cls.extract_local_deltas(txn),
            "gdelta": cls.extract_global_delta(txn),
            "lines": cls.extract_lines(txn, is_app),
            "trace": cls.extract_trace(txn, is_app),
        }

        result["bbr"] = BlackBoxResults.scrape(
            result["trace"], result["lines"]
        )

        return result


class SequenceAssertion:
    """Enable asserting invariants on a sequence of dry run executions"""

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

    def dryrun_assert(
        self,
        inputs: List[list],
        dryrun_results: List["DryRunTransactionResult"],
        assert_type: DryRunProperty,
    ):
        N = len(inputs)
        assert N == len(
            dryrun_results
        ), f"inputs (len={N}) and dryrun responses (len={len(dryrun_results)}) must have the same length"

        assert isinstance(
            assert_type, DryRunProperty
        ), f"assertions types must be DryRunAssertionType's but got [{assert_type}] which is a {type(assert_type)}"

        for i, args in enumerate(inputs):
            res = dryrun_results[i]
            actual = res.dig(assert_type)
            ok, msg = self(args, actual)
            assert ok, res.report(args, msg, row=i + 1)

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

    @classmethod
    def mode_has_assertion(
        cls, mode: ExecutionMode, assertion_type: DryRunProperty
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

    @classmethod
    def inputs_and_assertions(
        cls, scenario: Dict[str, Union[list, dict]], mode: ExecutionMode
    ) -> Tuple[List[tuple], Dict[DRProp, Any]]:
        """
        Validate that a Blackbox Test Scenario has been properly constructed, and return back
        its components which consist of **inputs** and _optional_ **assertions**.

        A scenario should adhere to the following schema:
        ```
        {
            "inputs":       List[Tuple[Union[str, int], ...]],
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
                assert isinstance(
                    key, DRProp
                ) and SequenceAssertion.mode_has_assertion(
                    mode, key
                ), f"each key must be a DryrunAssertionTypes appropriate to {mode}. This is not the case for key {key}"

        return inputs, assertions
