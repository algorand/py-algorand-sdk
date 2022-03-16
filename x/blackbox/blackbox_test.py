from collections import Counter
from pathlib import Path

import pytest

from algosdk.testing.dryrun import Helper as DryRunHelper
from algosdk.testing.teal_blackbox import (
    csv_from_dryrun_apps,
    csv_from_dryrun_logicsigs,
    dryrun_assert,
    get_blackbox_scenario_components,
    lightly_encode_args,
    lightly_encode_output,
    mode_has_assertion,
    DryRunAssertionType as DRA,
    Mode,
    SequenceAssertion,
)
from x.testnet import get_algod


# should this one be in `teal_blackbox.py` ?
def first_contains_second(first, second):
    for k, v in second.items():
        if k not in first or v != first[k]:
            return False
    return True


# should this one be in `teal_blackbox.py` ?
def scratch_encode(x) -> str:
    x = x.to_bytes(8, "big") if isinstance(x, int) else x.encode("utf-8")
    return f"0x{x.hex()}"


def fac_with_overflow(n):
    if n < 2:
        return 1
    if n > 20:
        return 2432902008176640000
    return n * fac_with_overflow(n - 1)


def fac_scratch(args, actual):
    n = args[0]
    fac = fac_with_overflow(n)
    app_case = {0: n, 1: fac} if n < 21 else {0: 21, 1: fac}
    return first_contains_second(app_case, actual)


def string_mult_status(args, actual):
    _, n = args
    if n == 0:
        return "REJECT"
    if n < 45:
        return "PASS"
    return actual in (
        "PASS",
        f"cost budget exceeded: budget is 700 but program cost was {30 + 15 * n}",
    )


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_last_log(args):
    n = args[0]
    return lightly_encode_output(fib(n), logs=True) if n else None


def fib_cost(args):
    cost = 17
    for n in range(1, args[0] + 1):
        cost += 31 * fib(n - 1)
    return cost


APP_SCENARIOS = {
    "app_exp": {
        "inputs": [()],
        # since only a single input, just assert a constant in each case
        "assertions": {
            DRA.cost: 11,
            # int assertions on log outputs need encoding to varuint-hex:
            DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            # dicts have a special meaning as assertions. So in the case of "finalScratch"
            # which is supposed to _ALSO_ output a dict, we need to use a lambda as a work-around
            DRA.finalScratch: lambda _: {0: 1024},
            DRA.stackTop: 1024,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    "app_square_byref": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.cost: lambda _, actual: 20 < actual < 22,
            DRA.lastLog: lightly_encode_output(1337, logs=True),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRA.finalScratch: lambda args, actual: (
                {2, 1337, (args[0] ** 2 if args[0] else 2)}
            ).issubset(set(actual.values())),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 3,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    "app_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.cost: 14,
            DRA.lastLog: {
                # since execution REJECTS for 0, expect last log for this case to be None
                (i,): lightly_encode_output(i * i, logs=True) if i else None
                for i in range(100)
            },
            DRA.finalScratch: lambda args: (
                {0: args[0], 1: args[0] ** 2} if args[0] else {}
            ),
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 2,
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRA.passed: lambda i: i[0] > 0,
            DRA.rejected: lambda i: i[0] == 0,
            DRA.noError: True,
        },
    },
    "app_swap": {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            DRA.cost: 27,
            DRA.lastLog: lightly_encode_output(1337, logs=True),
            DRA.finalScratch: lambda args, actual: first_contains_second(
                Counter(actual.values()),
                {scratch_encode(args[0]): 2, scratch_encode(args[1]): 1},
            ),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    "app_string_mult": {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            DRA.cost: lambda args: 30 + 15 * args[1],
            DRA.lastLog: (
                lambda args: lightly_encode_output(args[0] * args[1])
                if args[1]
                else None
            ),
            DRA.finalScratch: lambda args, actual: {
                args[1] + 1,
                scratch_encode(args[0]),
                scratch_encode(args[0] * (args[1] or 1)),
            }.issubset(set(actual.values())),
            DRA.stackTop: lambda args: args[1] * 4,
            DRA.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRA.status: string_mult_status,
            # to handle the nuance between logicsigs and apps would need to separate the next two:
            DRA.passed: (
                lambda args, actual: (0 < args[1] < 45 and actual is True)
                or (args[1] == 0 and actual is False)
                or (args[1] >= 45)
            ),
            DRA.rejected: (
                lambda args, actual: (args[1] == 0 and actual is True) or True
            ),
        },
    },
    "app_oldfac": {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            DRA.cost: lambda args, actual: (
                actual - 40 <= 17 * args[0] <= actual + 40
            ),
            DRA.lastLog: lambda args, actual: (actual is None)
            or (int(actual, base=16) == fac_with_overflow(args[0])),
            DRA.finalScratch: fac_scratch,
            DRA.stackTop: lambda args: fac_with_overflow(args[0]),
            DRA.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRA.status: lambda args, actual: (
                actual == "PASS" if args[0] < 21 else "overflowed" in actual
            ),
            DRA.passed: lambda args: args[0] < 21,
            DRA.rejected: False,
            DRA.noError: lambda args, actual: (
                True if args[0] < 21 else "overflowed" in actual
            ),
        },
    },
    "app_slow_fibonacci": {
        "inputs": [(i,) for i in range(15)],
        "assertions": {
            DRA.cost: fib_cost,
            DRA.lastLog: fib_last_log,
            DRA.finalScratch: lambda args, actual: (
                args[0] == 0
                or first_contains_second({0: args[0], 1: fib(args[0])}, actual)
            ),
            DRA.stackTop: lambda args: fib(args[0]),
            DRA.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRA.status: lambda args, actual: (
                actual == "REJECT"
                if args[0] == 0
                else (actual == "PASS" if args[0] < 8 else True)
            ),
            DRA.passed: lambda args, actual: (
                actual is False
                if args[0] == 0
                else (actual is True if args[0] < 8 else True)
            ),
            DRA.rejected: lambda args, actual: (
                actual is True
                if args[0] == 0
                else (actual is False if args[0] < 8 else True)
            ),
            DRA.noError: lambda args, actual: (
                actual if 0 < args[0] < 8 else True
            ),
        },
    },
}


@pytest.mark.parametrize("filebase", APP_SCENARIOS.keys())
def test_app_with_report(filebase: str):
    mode, scenario = Mode.Application, APP_SCENARIOS[filebase]

    # 0. Validate that the scenarios are well defined:
    inputs, assertions = get_blackbox_scenario_components(scenario, mode)

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

    # 2. Build the Dryrun requests:
    drbuilder = DryRunHelper.build_simple_app_request
    dryrun_reqs = list(
        map(lambda a: drbuilder(teal, lightly_encode_args(a)), inputs)
    )

    # 3. Run the requests to obtain sequence of Dryrun resonses:
    dryrun_resps = list(map(algod.dryrun, dryrun_reqs))

    # 4. Generate statistical report of all the runs:
    csvpath = path / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(csv_from_dryrun_apps(inputs, dryrun_resps))

    # 5. Sequential assertions (if provided any)
    for i, type_n_assertion in enumerate(assertions.items()):
        assert_type, assertion = type_n_assertion

        assert mode_has_assertion(
            mode, assert_type
        ), f"assert_type {assert_type} is not applicable for {mode}. Please REMOVE of MODIFY"

        assertion = SequenceAssertion(
            assertion, name=f"{case_name}[{i}]@{mode}-{assert_type}"
        )
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        dryrun_assert(inputs, dryrun_resps, assert_type, assertion)


# NOTE: logic sig dry runs are missing some information when compared with app dry runs.
# Therefore, certain assertions don't make sense for logic sigs explaining why some of the below are commented out:
LOGICSIG_SCENARIOS = {
    "lsig_exp": {
        "inputs": [()],
        "assertions": {
            # DRA.cost: 11,
            # DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            DRA.finalScratch: lambda _: {},
            DRA.stackTop: 1024,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    "lsig_square_byref": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.cost: lambda _, actual: 20 < actual < 22,
            # DRA.lastLog: lightly_encode_output(1337, logs=True),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRA.finalScratch: lambda args: (
                {0: args[0] ** 2} if args[0] else {}
            ),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 3,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    "lsig_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.cost: 14,
            # DRA.lastLog: {(i,): lightly_encode_output(i * i, logs=True) if i else None for i in range(100)},
            DRA.finalScratch: lambda args: ({0: args[0]} if args[0] else {}),
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 2,
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRA.passed: lambda i: i[0] > 0,
            DRA.rejected: lambda i: i[0] == 0,
            DRA.noError: True,
        },
    },
    "lsig_swap": {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            # DRA.cost: 27,
            # DRA.lastLog: lightly_encode_output(1337, logs=True),
            DRA.finalScratch: lambda args, actual: first_contains_second(
                Counter(actual.values()),
                {scratch_encode(args[0]): 2, scratch_encode(args[1]): 1},
            ),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    "lsig_string_mult": {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            # DRA.cost: lambda args: 30 + 15 * args[1],
            # DRA.lastLog: lambda args: lightly_encode_output(args[0] * args[1]) if args[1] else None,
            DRA.finalScratch: lambda args, actual: {
                args[1] + 1,
                scratch_encode(args[0]),
                scratch_encode(args[0] * (args[1] or 1)),
            }.issubset(set(actual.values())),
            DRA.stackTop: lambda args: args[1] * 4,
            DRA.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRA.status: string_mult_status,
            # to handle the nuance between logicsigs and apps would need to separate the next two:
            DRA.passed: (
                lambda args, actual: (0 < args[1] < 45 and actual is True)
                or (args[1] == 0 and actual is False)
                or (args[1] >= 45)
            ),
            DRA.rejected: (
                lambda args, actual: (args[1] == 0 and actual is True) or True
            ),
        },
    },
    "lsig_oldfac": {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            # DRA.cost: lambda args, actual: actual - 40 <= 17 * args[0] <= actual + 40,
            # DRA.lastLog: lambda args, actual: (actual is None) or (int(actual, base=16) == fac_with_overflow(args[0])),
            DRA.finalScratch: fac_scratch,
            DRA.stackTop: lambda args: fac_with_overflow(args[0]),
            DRA.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRA.status: lambda args, actual: (
                actual == "PASS" if args[0] < 21 else "overflowed" in actual
            ),
            DRA.passed: lambda args: args[0] < 21,
            DRA.rejected: False,
            DRA.noError: lambda args, actual: (
                True if args[0] < 21 else "overflowed" in actual
            ),
        },
    },
    "lsig_slow_fibonacci": {
        "inputs": [(i,) for i in range(15)],
        "assertions": {
            # DRA.cost: fib_cost,
            # DRA.lastLog: fib_last_log,
            DRA.finalScratch: lambda args, actual: (
                args[0] == 0
                or first_contains_second({0: args[0], 1: fib(args[0])}, actual)
            ),
            DRA.stackTop: lambda args: fib(args[0]),
            DRA.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRA.status: lambda args, actual: (
                actual == "REJECT"
                if args[0] == 0
                else (actual == "PASS" if args[0] < 8 else True)
            ),
            DRA.passed: lambda args, actual: (
                actual is False
                if args[0] == 0
                else (actual is True if args[0] < 8 else True)
            ),
            DRA.rejected: lambda args, actual: (
                actual is True
                if args[0] == 0
                else (actual is False if args[0] < 8 else True)
            ),
            DRA.noError: lambda args, actual: (
                actual if 0 < args[0] < 8 else True
            ),
        },
    },
}


@pytest.mark.parametrize("filebase", LOGICSIG_SCENARIOS.keys())
def test_logicsig_with_report(filebase: str):
    mode, scenario = Mode.Signature, LOGICSIG_SCENARIOS[filebase]

    # 0. Validate that the scenarios are well defined:
    inputs, assertions = get_blackbox_scenario_components(scenario, mode)

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

    # 2. Build the Dryrun requests:
    drbuilder = DryRunHelper.build_simple_logicsig_request
    dryrun_reqs = list(
        map(lambda a: drbuilder(teal, lightly_encode_args(a)), inputs)
    )

    # 3. Run the requests to obtain sequence of Dryrun resonses:
    dryrun_resps = list(map(algod.dryrun, dryrun_reqs))

    # 4. Generate statistical report of all the runs:
    csvpath = path / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(csv_from_dryrun_logicsigs(inputs, dryrun_resps))

    print(f"Saved Dry Run CSV report to {csvpath}")

    # 5. Sequential assertions (if provided any)
    for i, type_n_assertion in enumerate(assertions.items()):
        assert_type, assertion = type_n_assertion

        assert mode_has_assertion(
            mode, assert_type
        ), f"assert_type {assert_type} is not applicable for {mode}. Please REMOVE of MODIFY"

        assertion = SequenceAssertion(
            assertion, name=f"{case_name}[{i}]@{mode}-{assert_type}"
        )
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        dryrun_assert(inputs, dryrun_resps, assert_type, assertion)
