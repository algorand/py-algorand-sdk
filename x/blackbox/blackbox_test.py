from pathlib import Path

from algosdk.transaction import assign_group_id
from algosdk.v2client import algod
from algosdk.future.transaction import *

# from algosdk.dryrun_results import DryrunResponse

from .teal_blackbox import do_dryrun

TEAL = Path.cwd() / "x" / "blackbox" / "teal"

client = algod.AlgodClient("a" * 64, "http://localhost:4001")

test_cases = [
    ("demo succeed", "demo", ["succeed"]),
    ("demo FAIL", "demo", ["FAIL"]),
    ("new factorial", "fac_by_ref", []),
    ("old factorial", "old_fac", []),
    ("swap", "swapper", []),
    ("increment", "increment", []),
    ("tally", "tallygo", []),
    ("BAD factorial", "fac_by_ref_BAD", []),
]


def test_blackbox():
    for tcase, teal, args in test_cases:
        path = TEAL / (teal + ".teal")
        print(f"case={tcase}, approval_path={path}")
        with open(path) as f:
            approval = f.read()
            do_dryrun(tcase, client, approval, *args)
