from pathlib import Path
import pytest

from algosdk.transaction import assign_group_id
from algosdk.v2client import algod

# from algosdk.future.transaction import *

# from algosdk.dryrun_results import DryrunResponse

from .teal_blackbox import do_dryrun, cleanup, ApprovalBundle


TEAL = Path.cwd() / "x" / "blackbox" / "teal"


@pytest.fixture(scope="session", autouse=True)
def teardown():
    dummy = 42
    yield dummy
    cleanup()


test_cases = [
    # ("demo succeed", "demo", ["succeed"]),
    # ("demo FAIL", "demo", ["FAIL"]),
    # ("new factorial", "fac_by_ref", []),
    # ("old factorial", "old_fac", []),
    # ("swap", "swapper", []),
    # ("increment", "increment", []),
    # ("tally", "tallygo", []),
    # ("BAD factorial", "fac_by_ref_BAD", []),
    ("demo succeed", ApprovalBundle("demo"), ["succeed"]),
    ("demo FAIL", ApprovalBundle("demo"), ["FAIL"]),
    ("new factorial", ApprovalBundle("fac_by_ref"), []),
    ("old factorial", ApprovalBundle("old_fac"), []),
    ("swap", ApprovalBundle("swapper"), []),
    ("increment", ApprovalBundle("increment"), []),
    ("tally", ApprovalBundle("tallygo"), []),
    ("BAD factorial", ApprovalBundle("fac_by_ref_BAD"), []),
    # ("lots O vars", "lots_o_vars", []),
]


def test_blackbox():
    for tcase, approval, args in test_cases:
        path = TEAL / (approval.teal + ".teal")
        print(f"case={tcase}, approval_path={path}")
        with open(path) as f:
            approval.teal = f.read()
            do_dryrun(tcase, approval, *args)
