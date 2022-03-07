import operator
from pathlib import Path
import pytest

from algosdk.future.transaction import StateSchema
from algosdk.v2client import algod

from .teal_blackbox import (
    do_dryrun_reports,
    deep_blackbox,
    ApprovalBundle,
    BlackBoxAssertionType,
)

from .blacksand import cleanup

TEAL = Path.cwd() / "x" / "blackbox" / "teal"


@pytest.fixture(scope="session", autouse=True)
def teardown():
    yield
    cleanup()


reporting_cases = [
    ("demo succeed", ApprovalBundle("demo"), ["succeed"]),
    ("demo FAIL", ApprovalBundle("demo"), ["FAIL"]),
    ("new factorial", ApprovalBundle("fac_by_ref"), []),
    ("old factorial", ApprovalBundle("old_fac"), []),
    ("swap", ApprovalBundle("swapper"), []),
    ("increment", ApprovalBundle("increment"), []),
    ("tally", ApprovalBundle("tallygo"), []),
    ("BAD factorial", ApprovalBundle("fac_by_ref_BAD"), []),
    ("Wilt", ApprovalBundle("wilt_the_stilt"), []),
    (
        "lots O vars",
        ApprovalBundle(
            "lots_o_vars",
            local_schema=StateSchema(num_uints=2, num_byte_slices=2),
            global_schema=StateSchema(num_uints=2, num_byte_slices=2),
        ),
        [39, 100, 42, "fourty two"],
    ),
]


def test_blackbox_with_report():
    for tcase, approval, args in reporting_cases:
        path = TEAL / (approval.teal + ".teal")
        print(f"case={tcase}, approval_path={path}")
        with open(path) as f:
            approval.teal = f.read()
            do_dryrun_reports(tcase, approval, args, col_max=50)


def fac_by_ref_args_expectations():
    def fac(n):
        if n < 2:
            return 1
        return n * fac(n - 1)

    def expected_cost(n):
        return 10 * n ** 2 + 28

    def expected_stack_height(n):
        return (n + 1) * 3

    def expected_scratch_state(n):
        return {2: fac(n)}

    def expected_is_contained_by_actual(expected, actual):
        return all(k in actual and actual[k] == v for k, v in expected.items())

    input_cases = [[n] for n in range(16)]
    return {
        "input_cases": input_cases,
        "expectations": {
            BlackBoxAssertionType.FINAL_STACK_TOP: {
                "func": fac,
            },
            BlackBoxAssertionType.LAST_LOG: {
                "func": lambda n: None,
            },
            BlackBoxAssertionType.COST: {
                "func": expected_cost,
                "op": operator.ge,
            },
            BlackBoxAssertionType.MAX_STACK_HEIGHT: {
                "func": expected_stack_height,
                "op": operator.ge,
            },
            BlackBoxAssertionType.FINAL_SCRATCH_STATE: {
                "func": expected_scratch_state,
                "op": expected_is_contained_by_actual,
            },
        },
    }


blackbox_cases = [
    (
        "new factorial",
        ApprovalBundle("fac_by_ref_args"),
        fac_by_ref_args_expectations(),
    ),
]


def test_teal_blackbox():
    for tcase, approval, scenarios in blackbox_cases:
        path = TEAL / (approval.teal + ".teal")
        print(f"case={tcase}, approval_path={path}")
        with open(path) as f:
            approval.teal = f.read()
            deep_blackbox(tcase, approval, scenarios)
