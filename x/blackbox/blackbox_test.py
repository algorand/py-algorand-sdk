from pathlib import Path

import pytest

from algosdk.testing.dryrun import Helper as DryRunHelper
from algosdk.testing.teal_blackbox import (
    DryRunEncoder as Encoder,
    DryRunExecutor as Executor,
    DryRunProperty as DRProp,
    DryRunTransactionResult as DRR,
    ExecutionMode,
    SequenceAssertion,
)
from x.testnet import get_algod


def fac_with_overflow(n):
    if n < 2:
        return 1
    if n > 20:
        return 2432902008176640000
    return n * fac_with_overflow(n - 1)


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_cost(args):
    cost = 17
    for n in range(1, args[0] + 1):
        cost += 31 * fib(n - 1)
    return cost


def test_singleton_assertions():
    algod = get_algod()
    algod_status = algod.status()
    assert algod_status

    teal_fmt = """#pragma version 6
{} 0
btoi
callsub square_0
{}
return

// square
square_0:
store 0
load 0
pushint 2 // 2
exp
retsub"""

    teal_app, teal_lsig = list(
        map(lambda s: teal_fmt.format(s, ""), ["txna ApplicationArgs", "arg"])
    )

    teal_app_log, bad_teal_lsig = list(
        map(
            lambda s: teal_fmt.format(
                s,
                """store 1
load 1
itob
log
load 1""",
            ),
            ["txna ApplicationArgs", "arg"],
        )
    )

    x = 9
    args = [x]

    app_res, app_log_res = list(
        map(
            lambda teal: Executor.dryrun_app(algod, teal, args),
            [teal_app, teal_app_log],
        )
    )
    lsig_res, bad_lsig_res = list(
        map(
            lambda teal: Executor.dryrun_logicsig(algod, teal, args),
            [teal_lsig, bad_teal_lsig],
        )
    )

    assert isinstance(app_res, DRR)
    assert isinstance(app_log_res, DRR)
    assert isinstance(lsig_res, DRR)
    assert isinstance(bad_lsig_res, DRR)

    assert app_res.mode == ExecutionMode.Application
    assert app_log_res.mode == ExecutionMode.Application
    assert lsig_res.mode == ExecutionMode.Signature
    assert bad_lsig_res.mode == ExecutionMode.Signature

    def prop_assert(dr_resp, actual, expected):
        assert expected == actual, dr_resp.report(
            args, f"expected {expected} but got {actual}"
        )

    prop_assert(app_res, app_res.cost(), 9)
    prop_assert(app_log_res, app_log_res.cost(), 14)
    prop_assert(lsig_res, lsig_res.cost(), None)

    prop_assert(app_res, app_res.last_log(), None)
    prop_assert(
        app_log_res, app_log_res.last_log(), (x ** 2).to_bytes(8, "big").hex()
    )
    prop_assert(app_log_res, app_log_res.last_log(), Encoder.hex(x ** 2))
    prop_assert(lsig_res, lsig_res.last_log(), None)

    prop_assert(app_res, app_res.final_scratch(), {0: x})
    prop_assert(app_log_res, app_log_res.final_scratch(), {0: x, 1: x ** 2})
    prop_assert(lsig_res, lsig_res.final_scratch(), {0: x})
    prop_assert(bad_lsig_res, bad_lsig_res.final_scratch(), {0: x, 1: x ** 2})

    prop_assert(app_res, app_res.stack_top(), x ** 2)
    prop_assert(app_log_res, app_log_res.stack_top(), x ** 2)
    prop_assert(lsig_res, lsig_res.stack_top(), x ** 2)
    prop_assert(bad_lsig_res, bad_lsig_res.stack_top(), Encoder.hex0x(x ** 2))

    prop_assert(app_res, app_res.max_stack_height(), 2)
    prop_assert(app_log_res, app_log_res.max_stack_height(), 2)
    prop_assert(lsig_res, lsig_res.max_stack_height(), 2)
    prop_assert(bad_lsig_res, bad_lsig_res.max_stack_height(), 2)

    prop_assert(app_res, app_res.status(), "PASS")
    prop_assert(app_log_res, app_log_res.status(), "PASS")
    prop_assert(lsig_res, lsig_res.status(), "PASS")
    prop_assert(bad_lsig_res, bad_lsig_res.status(), "REJECT")

    prop_assert(app_res, app_res.passed(), True)
    prop_assert(app_log_res, app_log_res.passed(), True)
    prop_assert(lsig_res, lsig_res.passed(), True)
    prop_assert(bad_lsig_res, bad_lsig_res.passed(), False)

    prop_assert(app_res, app_res.rejected(), False)
    prop_assert(app_log_res, app_log_res.rejected(), False)
    prop_assert(lsig_res, lsig_res.rejected(), False)
    prop_assert(bad_lsig_res, bad_lsig_res.rejected(), True)

    prop_assert(app_res, app_res.rejected(), False)
    prop_assert(app_log_res, app_log_res.rejected(), False)
    prop_assert(lsig_res, lsig_res.rejected(), False)
    prop_assert(bad_lsig_res, bad_lsig_res.rejected(), True)

    prop_assert(app_res, app_res.error(), False)
    prop_assert(app_log_res, app_log_res.error(), False)
    prop_assert(lsig_res, lsig_res.error(), False)
    prop_assert(bad_lsig_res, bad_lsig_res.error(), True)
    assert (
        bad_lsig_res.error(
            pattern="logic 0 failed at line 7: log not allowed in current mode"
        )
        is True
    )
    prop_assert(
        bad_lsig_res, bad_lsig_res.error(pattern="log not allowed"), True
    )
    prop_assert(
        bad_lsig_res, bad_lsig_res.error(pattern="WRONG PATTERN"), False
    )

    prop_assert(app_res, app_res.noError(), True)
    prop_assert(app_log_res, app_log_res.noError(), True)
    prop_assert(lsig_res, lsig_res.noError(), True)
    assert (
        "logic 0 failed at line 7: log not allowed in current mode"
        in bad_lsig_res.noError()
    )


APP_SCENARIOS = {
    "app_exp": {
        "inputs": [()],
        # since only a single input, just assert a constant in each case
        "assertions": {
            DRProp.cost: 11,
            # int assertions on log outputs need encoding to varuint-hex:
            DRProp.lastLog: Encoder.hex(2 ** 10),
            # dicts have a special meaning as assertions. So in the case of "finalScratch"
            # which is supposed to _ALSO_ output a dict, we need to use a lambda as a work-around
            DRProp.finalScratch: lambda _: {0: 2 ** 10},
            DRProp.stackTop: 2 ** 10,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.noError: True,
        },
    },
    "app_square_byref": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRProp.cost: lambda _, actual: 20 < actual < 22,
            DRProp.lastLog: Encoder.hex(1337),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRProp.finalScratch: lambda args, actual: (
                {2, 1337, (args[0] ** 2 if args[0] else 2)}
            ).issubset(set(actual.values())),
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 3,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.noError: True,
        },
    },
    "app_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRProp.cost: 14,
            DRProp.lastLog: {
                # since execution REJECTS for 0, expect last log for this case to be None
                (i,): Encoder.hex(i * i) if i else None
                for i in range(100)
            },
            DRProp.finalScratch: lambda args: (
                {0: args[0], 1: args[0] ** 2} if args[0] else {}
            ),
            DRProp.stackTop: lambda args: args[0] ** 2,
            DRProp.maxStackHeight: 2,
            DRProp.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRProp.passed: lambda i: i[0] > 0,
            DRProp.rejected: lambda i: i[0] == 0,
            DRProp.noError: True,
        },
    },
    "app_swap": {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            DRProp.cost: 27,
            DRProp.lastLog: Encoder.hex(1337),
            DRProp.finalScratch: lambda args: {
                0: 4,
                1: 5,
                2: Encoder.hex0x(args[0]),
                3: 1337,
                4: Encoder.hex0x(args[1]),
                5: Encoder.hex0x(args[0]),
            },
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.noError: True,
        },
    },
    "app_string_mult": {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            DRProp.cost: lambda args: 30 + 15 * args[1],
            DRProp.lastLog: (
                lambda args: Encoder.hex(args[0] * args[1])
                if args[1]
                else None
            ),
            # due to dryrun 0-scratchvar artifact, special case for i == 0:
            DRProp.finalScratch: lambda args: (
                {
                    0: 5,
                    1: args[1],
                    2: args[1] + 1,
                    3: Encoder.hex0x(args[0]),
                    4: Encoder.hex0x(args[0] * args[1]),
                    5: Encoder.hex0x(args[0] * args[1]),
                }
                if args[1]
                else {
                    0: 5,
                    2: args[1] + 1,
                    3: Encoder.hex0x(args[0]),
                }
            ),
            DRProp.stackTop: lambda args: len(args[0] * args[1]),
            DRProp.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRProp.status: lambda args: (
                "PASS" if 0 < args[1] < 45 else "REJECT"
            ),
            DRProp.passed: lambda args: 0 < args[1] < 45,
            DRProp.rejected: lambda args: 0 >= args[1] or args[1] >= 45,
            DRProp.noError: True,
        },
    },
    "app_oldfac": {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            DRProp.cost: lambda args, actual: (
                actual - 40 <= 17 * args[0] <= actual + 40
            ),
            DRProp.lastLog: lambda args: (
                Encoder.hex(fac_with_overflow(args[0]))
                if args[0] < 21
                else None
            ),
            DRProp.finalScratch: lambda args: (
                {0: args[0], 1: fac_with_overflow(args[0])}
                if 0 < args[0] < 21
                else (
                    {0: min(21, args[0])}
                    if args[0]
                    else {1: fac_with_overflow(args[0])}
                )
            ),
            DRProp.stackTop: lambda args: fac_with_overflow(args[0]),
            DRProp.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRProp.status: lambda args: "PASS" if args[0] < 21 else "REJECT",
            DRProp.passed: lambda args: args[0] < 21,
            DRProp.rejected: lambda args: args[0] >= 21,
            DRProp.noError: lambda args, actual: (
                actual is True if args[0] < 21 else "overflowed" in actual
            ),
        },
    },
    "app_slow_fibonacci": {
        "inputs": [(i,) for i in range(18)],
        "assertions": {
            DRProp.cost: lambda args: (
                fib_cost(args) if args[0] < 17 else 70_000
            ),
            DRProp.lastLog: lambda args: (
                Encoder.hex(fib(args[0])) if 0 < args[0] < 17 else None
            ),
            DRProp.finalScratch: lambda args, actual: (
                actual == {0: args[0], 1: fib(args[0])}
                if 0 < args[0] < 17
                else (True if args[0] >= 17 else actual == {})
            ),
            # we declare to "not care" about the top of the stack for n >= 17
            DRProp.stackTop: lambda args, actual: (
                actual == fib(args[0]) if args[0] < 17 else True
            ),
            # similarly, we don't care about max stack height for n >= 17
            DRProp.maxStackHeight: lambda args, actual: (
                actual == max(2, 2 * args[0]) if args[0] < 17 else True
            ),
            DRProp.status: lambda args: "PASS"
            if 0 < args[0] < 8
            else "REJECT",
            DRProp.passed: lambda args: 0 < args[0] < 8,
            DRProp.rejected: lambda args: 0 >= args[0] or args[0] >= 8,
            DRProp.noError: lambda args, actual: (
                actual is True
                if args[0] < 17
                else "dynamic cost budget exceeded" in actual
            ),
        },
    },
}


@pytest.mark.parametrize("filebase", APP_SCENARIOS.keys())
def test_app_with_report(filebase: str):
    mode, scenario = ExecutionMode.Application, APP_SCENARIOS[filebase]

    # 0. Validate that the scenarios are well defined:
    inputs, assertions = SequenceAssertion.inputs_and_assertions(
        scenario, mode
    )

    algod = get_algod()

    # 1. Read the TEAL from ./x/blackbox/teal/*.teal
    path = Path.cwd() / "x" / "blackbox" / "teal"
    case_name = filebase
    tealpath = path / f"{filebase}.teal"
    with open(tealpath, "r") as f:
        teal = f.read()

    print(
        f"""Sandbox test and report {mode} for {case_name} from {tealpath}. TEAL is:
-------
{teal}
-------"""
    )

    # 2. Run the requests to obtain sequence of Dryrun responses:
    dryrun_results = Executor.dryrun_app_on_sequence(algod, teal, inputs)

    # 3. Generate statistical report of all the runs:
    csvpath = path / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(DRR.csv_report(inputs, dryrun_results))

    print(f"Saved Dry Run CSV report to {csvpath}")

    # 4. Sequential assertions (if provided any)
    for i, type_n_assertion in enumerate(assertions.items()):
        assert_type, assertion = type_n_assertion

        assert SequenceAssertion.mode_has_assertion(
            mode, assert_type
        ), f"assert_type {assert_type} is not applicable for {mode}. Please REMOVE or MODIFY"

        assertion = SequenceAssertion(
            assertion, name=f"{case_name}[{i}]@{mode}-{assert_type}"
        )
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        assertion.dryrun_assert(inputs, dryrun_results, assert_type)


# NOTE: logic sig dry runs are missing some information when compared with app dry runs.
# Therefore, certain assertions don't make sense for logic sigs explaining why some of the below are commented out:
LOGICSIG_SCENARIOS = {
    "lsig_exp": {
        "inputs": [()],
        "assertions": {
            # DRA.cost: 11,
            # DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            DRProp.finalScratch: lambda _: {},
            DRProp.stackTop: 2 ** 10,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.noError: True,
        },
    },
    "lsig_square_byref": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.cost: lambda _, actual: 20 < actual < 22,
            # DRA.lastLog: lightly_encode_output(1337, logs=True),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRProp.finalScratch: lambda args: (
                {0: args[0] ** 2} if args[0] else {}
            ),
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 3,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.noError: True,
        },
    },
    "lsig_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.cost: 14,
            # DRA.lastLog: {(i,): lightly_encode_output(i * i, logs=True) if i else None for i in range(100)},
            DRProp.finalScratch: lambda args: (
                {0: args[0]} if args[0] else {}
            ),
            DRProp.stackTop: lambda args: args[0] ** 2,
            DRProp.maxStackHeight: 2,
            DRProp.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRProp.passed: lambda i: i[0] > 0,
            DRProp.rejected: lambda i: i[0] == 0,
            DRProp.noError: True,
        },
    },
    "lsig_swap": {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            # DRA.cost: 27,
            # DRA.lastLog: lightly_encode_output(1337, logs=True),
            DRProp.finalScratch: lambda args: {
                0: Encoder.hex0x(args[1]),
                1: Encoder.hex0x(args[0]),
                3: 1,
                4: Encoder.hex0x(args[0]),
            },
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.noError: True,
        },
    },
    "lsig_string_mult": {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            # DRA.cost: lambda args: 30 + 15 * args[1],
            # DRA.lastLog: lambda args: lightly_encode_output(args[0] * args[1]) if args[1] else None,
            DRProp.finalScratch: lambda args: (
                {
                    0: Encoder.hex0x(args[0] * args[1]),
                    2: args[1],
                    3: args[1] + 1,
                    4: Encoder.hex0x(args[0]),
                }
                if args[1]
                else {
                    3: args[1] + 1,
                    4: Encoder.hex0x(args[0]),
                }
            ),
            DRProp.stackTop: lambda args: len(args[0] * args[1]),
            DRProp.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRProp.status: lambda args: "PASS" if args[1] else "REJECT",
            DRProp.passed: lambda args: bool(args[1]),
            DRProp.rejected: lambda args: not bool(args[1]),
            DRProp.noError: True,
        },
    },
    "lsig_oldfac": {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            # DRA.cost: lambda args, actual: actual - 40 <= 17 * args[0] <= actual + 40,
            # DRA.lastLog: lambda args, actual: (actual is None) or (int(actual, base=16) == fac_with_overflow(args[0])),
            DRProp.finalScratch: lambda args: (
                {0: min(args[0], 21)} if args[0] else {}
            ),
            DRProp.stackTop: lambda args: fac_with_overflow(args[0]),
            DRProp.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRProp.status: lambda args: "PASS" if args[0] < 21 else "REJECT",
            DRProp.passed: lambda args: args[0] < 21,
            DRProp.rejected: lambda args: args[0] >= 21,
            DRProp.noError: lambda args, actual: (
                actual is True
                if args[0] < 21
                else "logic 0 failed at line 21: * overflowed" in actual
            ),
        },
    },
    "lsig_slow_fibonacci": {
        "inputs": [(i,) for i in range(18)],
        "assertions": {
            # DRA.cost: fib_cost,
            # DRA.lastLog: fib_last_log,
            # by returning True for n >= 15, we're declaring that we don't care about the scratchvar's for such cases:
            DRProp.finalScratch: lambda args, actual: (
                actual == {0: args[0]}
                if 0 < args[0] < 15
                else (True if args[0] else actual == {})
            ),
            DRProp.stackTop: lambda args, actual: (
                actual == fib(args[0]) if args[0] < 15 else True
            ),
            DRProp.maxStackHeight: lambda args, actual: (
                actual == max(2, 2 * args[0]) if args[0] < 15 else True
            ),
            DRProp.status: lambda args: "PASS"
            if 0 < args[0] < 15
            else "REJECT",
            DRProp.passed: lambda args: 0 < args[0] < 15,
            DRProp.rejected: lambda args: not (0 < args[0] < 15),
            DRProp.noError: lambda args, actual: (
                actual is True
                if args[0] < 15
                else "dynamic cost budget exceeded" in actual
            ),
        },
    },
}


@pytest.mark.parametrize("filebase", LOGICSIG_SCENARIOS.keys())
def test_logicsig_with_report(filebase: str):
    mode, scenario = ExecutionMode.Signature, LOGICSIG_SCENARIOS[filebase]

    # 0. Validate that the scenarios are well defined:
    inputs, assertions = SequenceAssertion.inputs_and_assertions(
        scenario, mode
    )

    algod = get_algod()

    # 1. Read the TEAL from ./x/blackbox/teal/*.teal
    path = Path.cwd() / "x" / "blackbox" / "teal"
    case_name = filebase
    tealpath = path / f"{filebase}.teal"
    with open(tealpath, "r") as f:
        teal = f.read()

    print(
        f"""Sandbox test and report {mode} for {case_name} from {tealpath}. TEAL is:
-------
{teal}
-------"""
    )

    # 2. Run the requests to obtain sequence of Dryrun resonses:
    dryrun_results = Executor.dryrun_logicsig_on_sequence(algod, teal, inputs)

    # 3. Generate statistical report of all the runs:
    csvpath = path / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(DRR.csv_report(inputs, dryrun_results))

    print(f"Saved Dry Run CSV report to {csvpath}")

    # 4. Sequential assertions (if provided any)
    for i, type_n_assertion in enumerate(assertions.items()):
        assert_type, assertion = type_n_assertion

        assert SequenceAssertion.mode_has_assertion(
            mode, assert_type
        ), f"assert_type {assert_type} is not applicable for {mode}. Please REMOVE of MODIFY"

        assertion = SequenceAssertion(
            assertion, name=f"{case_name}[{i}]@{mode}-{assert_type}"
        )
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        assertion.dryrun_assert(inputs, dryrun_results, assert_type)
