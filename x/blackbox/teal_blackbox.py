from base64 import b64decode
from contextlib import contextmanager
from dataclasses import dataclass
from email.policy import default
from glom import glom
from inspect import stack
from tabulate import tabulate
from typing import Any, Generator, List, Optional, Set

from algosdk.v2client.algod import AlgodClient

from algosdk.future.transaction import (
    ApplicationCallTxn,
    ApplicationClearStateTxn,
    ApplicationOptInTxn,
    ApplicationCreateTxn,
    ApplicationDeleteTxn,
    LogicSigAccount,
    LogicSigTransaction,
    OnComplete,
    SignedTransaction,
    StateSchema,
    SuggestedParams,
    assign_group_id,
    create_dryrun,
    wait_for_confirmation,
)
from algosdk.kmd import KMDClient
import algosdk.logic as logic


CLEAR_TEAL = """{}
pushint 1
return"""

# TODO: Can we skip the logic sig altogether?
LOGIC_SIG_TEAL = """{}
pushint 1"""


SB_ALGOD_ADDRESS = "http://localhost:4001"
SB_ALGOD_TOKEN = "a" * 64

SB_KMD_ADDRESS = "http://localhost:4002"
SB_KMD_TOKEN = "a" * 64

SB_KMD_WALLET_NAME = "unencrypted-default-wallet"
SB_KMD_WALLET_PASSWORD = ""

ZERO_SCHEMA = StateSchema(num_uints=0, num_byte_slices=0)


@dataclass
class AddressAndSecret:
    address: str
    secret: str


@dataclass
class ApplicationBundle:
    author: AddressAndSecret
    sp: SuggestedParams
    approval_src: str
    approval: bytes
    clear_src: str
    clear: bytes
    local_schema: StateSchema
    global_schema: StateSchema
    create_txn: ApplicationCreateTxn
    signed_txn: SignedTransaction
    txid: str
    resp: dict
    index: int
    address: str


class DryRunContext:
    def __init__(
        self,
        algod: AlgodClient,
        creator: AddressAndSecret,
        clear_src: str = CLEAR_TEAL,
        lsig_src: str = LOGIC_SIG_TEAL,
    ):
        self.algod = algod
        self.creator = creator
        self.clear_src_tmpl = clear_src

        self.lsig_src_tmpl = lsig_src
        self.lsig_src: str
        self.lsig: bytes
        self.lsig_account: LogicSigAccount

    @contextmanager
    def application(
        self,
        approval_src: str,
        local_schema: StateSchema = ZERO_SCHEMA,
        global_schema: StateSchema = ZERO_SCHEMA,
        wait_rounds: int = 3,
    ) -> Generator[ApplicationBundle, None, None]:
        lines = approval_src.split("\n")
        pragma = lines[0]
        sp = self.algod.suggested_params()

        clear_src: str = self.clear_src_tmpl.format(pragma)
        clear: bytes = b64decode(self.algod.compile(clear_src)["result"])

        self.lsig_src = self.lsig_src_tmpl.format(pragma)
        self.lsig = b64decode(self.algod.compile(self.lsig_src)["result"])
        self.lsig_account = LogicSigAccount(self.lsig)

        approval = b64decode(self.algod.compile(approval_src)["result"])

        # Create and simultaneously opt-in to the app I just created:
        create = ApplicationCreateTxn(
            self.creator.address,
            sp,
            OnComplete.OptInOC,
            approval,
            clear,
            local_schema,
            global_schema,
        )
        signed = create.sign(self.creator.secret)
        txid = self.algod.send_transaction(signed)
        res = wait_for_confirmation(self.algod, txid, wait_rounds)

        app_id = res["application-index"]
        app_addr = logic.get_application_address(app_id)

        # optin = ApplicationOptInTxn(self.creator.address, sp, app_id)
        # signed = optin.sign(self.creator.secret)
        # txid = self.algod.send_transaction(signed)
        res = wait_for_confirmation(self.algod, txid, wait_rounds)

        app = ApplicationBundle(
            self.creator,
            sp,
            approval_src,
            approval,
            clear_src,
            clear,
            local_schema,
            global_schema,
            create,
            signed,
            txid,
            res,
            app_id,
            app_addr,
        )
        try:
            print(f"Created app with index={app_id}")
            yield app
        finally:
            addr = self.creator.address
            account_info = self.algod.account_info(addr)
            apps_opted_in = account_info["apps-local-state"]
            optin_ids = [a["id"] for a in apps_opted_in]

            apps_created = account_info["created-apps"]
            created_ids = [a["id"] for a in apps_created]
            print(
                f"""Before commencing, creator [{addr}] currently has:
* {len(apps_opted_in)} opted-in apps
    * indices: {', '.join(str(x) for x in optin_ids)}
* {len(apps_created)} created apps
    * indices: {', '.join(str(x) for x in created_ids)}
"""
            )

            sp = self.algod.suggested_params()

            print(f"Gonna delete app with index={app_id}")

            if app_id not in optin_ids:
                app_optin = ApplicationOptInTxn(
                    self.creator.address, sp, app_id
                )
                app_delete = ApplicationDeleteTxn(
                    self.creator.address, sp, app_id
                )
                assign_group_id([app_optin, app_delete])
                signed_optin = app_optin.sign(self.creator.secret)
                signed_delete = app_delete.sign(self.creator.secret)
                delete_txn = self.algod.send_transactions(
                    [signed_optin, signed_delete]
                )
            else:
                app_delete = ApplicationDeleteTxn(
                    self.creator.address, sp, app_id
                )
                signed_delete = app_delete.sign(self.creator.secret)
                delete_txn = self.algod.send_transaction(signed_delete)

            print(f"Gonna clear out of app with index={app_id}")
            app_clear = ApplicationClearStateTxn(addr, sp, app_id)
            signed_clear = app_clear.sign(self.creator.secret)
            clear_txn = self.algod.send_transaction(signed_clear)

            delete_resp = wait_for_confirmation(self.algod, delete_txn, 3)
            clear_resp = wait_for_confirmation(self.algod, clear_txn, 3)


def cleanup():
    print("\n\n\n --------- TEARDOWN --------- \n\n")
    creator = get_creator()
    addr = creator.address
    pk = creator.secret
    algod = get_algod()
    sp = algod.suggested_params()
    account_info = algod.account_info(addr)

    apps_created = account_info["created-apps"]
    print(
        f"""Gonna tear down {len(apps_created)} apps for account {addr}
These have indexes: {','.join(str(a['id']) for a in apps_created)}"""
    )
    for app in apps_created:
        index = app["id"]
        app_delete = ApplicationDeleteTxn(addr, sp, index)
        signed_delete = app_delete.sign(pk)
        deleteid = algod.send_transaction(signed_delete)
        delete_resp = wait_for_confirmation(algod, deleteid, 3)
        x = 42

    apps_opted_in = account_info["apps-local-state"]
    print(
        f"""Gonna clear out of {len(apps_opted_in)} apps for account {addr}
These have indexes: {','.join(str(a['id']) for a in apps_opted_in)}"""
    )
    for app in apps_opted_in:
        index = app["id"]
        app_clear = ApplicationClearStateTxn(addr, sp, index)
        signed_clear = app_clear.sign(pk)
        clearid = algod.send_transaction(signed_clear)
        close_resp = wait_for_confirmation(algod, clearid, 3)


def _get_accounts(kmd: KMDClient = None):
    if not kmd:
        kmd = KMDClient(SB_KMD_TOKEN, SB_KMD_ADDRESS)
    wallets = kmd.list_wallets()

    walletID = None
    for wallet in wallets:
        if wallet["name"] == SB_KMD_WALLET_NAME:
            walletID = wallet["id"]
            break

    if walletID is None:
        raise Exception("Wallet not found: {}".format(SB_KMD_WALLET_NAME))

    walletHandle = kmd.init_wallet_handle(walletID, SB_KMD_WALLET_PASSWORD)

    try:
        addresses = kmd.list_keys(walletHandle)
        privateKeys = [
            kmd.export_key(walletHandle, SB_KMD_WALLET_PASSWORD, addr)
            for addr in addresses
        ]
        kmdAccounts = [
            (addresses[i], privateKeys[i]) for i in range(len(privateKeys))
        ]
    finally:
        kmd.release_wallet_handle(walletHandle)

    return kmdAccounts


def get_account_addresses(kmd: KMDClient = None) -> List[AddressAndSecret]:
    return [AddressAndSecret(addr, pk) for addr, pk in _get_accounts(kmd)]


def get_creator(kmd: KMDClient = None) -> AddressAndSecret:
    return get_account_addresses(kmd)[0]


def get_algod() -> AlgodClient:
    return AlgodClient(SB_ALGOD_TOKEN, SB_ALGOD_ADDRESS)


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


def trace_table(trace: List[dict], lines: List[str], col_max: int) -> str:
    black_box_result = essential_info(trace, lines)
    # pcs, tls, N, stacks, scratches, slots_used = list(map(getattr(

    rows = [
        map(
            str,
            [
                i + 1,
                black_box_result.program_counters[i],
                black_box_result.teal_source_lines[i],
                black_box_result.stack_evolution[i],
                *black_box_result.stack_evolution[i],
            ],
        )
        for i in range(black_box_result.program_length)
    ]
    if col_max and col_max > 0:
        rows = [[x[:col_max] for x in row] for row in rows]
    table = tabulate(
        rows,
        headers=[
            "L#",
            "PC#",
            "Teal",
            "Stack",
            *(f"S@{s}" for s in black_box_result.slots_used),
        ],
        tablefmt="presto",
    )
    return table


@dataclass
class BlackBoxResults:
    program_length: int
    program_counters: int
    teal_source_lines: List[str]
    stack_evolution: List[list]
    scratch_evolution: List[list]
    slots_used: List[int]
    raw_stacks: List[list]

    def assert_well_defined(self):
        assert all(
            self.program_length == len(x)
            for x in (
                self.program_counters,
                self.teal_source_lines,
                self.stack_evolution,
                self.scratch_evolution,
            )
        )

    def __str__(self) -> str:
        return f"BlackBoxResult(program_length={self.program_length})"


def essential_info(trace, lines):
    pcs = [t["pc"] for t in trace]

    tls = [lines[t["line"] - 1] for t in trace]
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
    scratches = [
        [f"{i}->{scratch[i]}" if i in scratch else "" for i in slots_used]
        for scratch in scratches
    ]
    assert N == len(
        scratches
    ), f"mismatch of lengths in tls v. scratches ({N} v. {len(scratches)})"

    bbr = BlackBoxResults(
        N, pcs, tls, stacks, scratches, slots_used, raw_stacks
    )
    bbr.assert_well_defined()
    return bbr


@dataclass
class ApprovalBundle:
    teal: str
    local_schema: StateSchema = ZERO_SCHEMA
    global_schema: StateSchema = ZERO_SCHEMA


class DryRunTester:
    def __init__(
        self,
        name: str,
        dry_run_response: dict,
        creator_address: str,
        testing_txn_index: int = 0,
        col_max: int = None,
    ):
        self.name = name
        self.resp = dry_run_response
        self.creator_address = creator_address
        self.testing_idx = testing_txn_index
        self.col_max = col_max

        self.black_box_results = [
            essential_info(tx["app-call-trace"], tx["disassembly"])
            for tx in self.resp["txns"]
        ]
        for bbr in self.black_box_results:
            bbr.assert_well_defined()

    ### methods that pivot of testing idx ###
    def testing_txn(self, idx: int = None) -> dict:
        if idx is None:
            idx = self.testing_idx
        return self.resp["txns"][idx]

    def last_log(self, idx: int = None) -> Optional[str]:
        if idx is None:
            idx = self.testing_idx
        logs = self.logs(idx)
        return logs[-1] if logs else None

    def logs(self, idx: int = None) -> List[str]:
        if idx is None:
            idx = self.testing_idx
        return self.resp["txns"][idx].get("logs", [])

    def get_black_box_result(self, idx: int = None) -> BlackBoxResults:
        if idx is None:
            idx = self.testing_idx
        return self.black_box_results[idx]

    def last_stack_value(self, idx: int = None) -> Optional[TealVal]:
        last_stack = self.get_black_box_result(idx).raw_stacks[-1]
        return last_stack[-1] if last_stack else None

    def slots_used(self, idx: int = None) -> Set[int]:
        return self.get_black_box_result(idx).slots_used

    def _global_x_used(self, x: str, idx: int = None) -> int:
        gdeltas = self.testing_txn(idx).get("global-delta", [])
        return len(
            [
                gd
                for gd in gdeltas
                if glom(gd, f"value.{x}", default=False) is not False
            ]
        )

    def global_bytes_used(self, idx: int = None) -> int:
        return self._global_x_used("bytes", idx)

    def global_uints_used(self, idx: int = None) -> int:
        return self._global_x_used("uint", idx)

    def _local_x_used(self, x: str, idx: int = None) -> int:
        """Not sure this is correct"""
        ldeltas = [
            ld
            for ld in self.testing_txn(idx).get("local-deltas", [])
            if ld["address"] == self.creator_address
        ]
        if not ldeltas:
            return 0
        assert len(ldeltas) == 1
        ldelta = ldeltas[0]["delta"]
        return len(
            [
                ld
                for ld in ldelta
                if glom(ld, f"value.{x}", default=False) is not False
            ]
        )

    def local_bytes_used(self, idx: int = None) -> int:
        return self._local_x_used("bytes", idx)

    def local_uints_used(self, idx: int = None) -> int:
        return self._local_x_used("uints", idx)

    ### human readable summary ###

    def report(self) -> str:
        bookend = f"""
        <<<<<<{self.name}>>>>>>
REPORTS FOR {len(self.resp["txns"])} TRANSACTIONS
DEFAULT TXN TESTING-INDEX: {self.testing_idx}
BLACK BOX RESULT: {self.get_black_box_result()}
FINAL LOG: {self.last_log()}
TOP OF STACK: {self.last_stack_value()!r}
SLOTS USED: {self.slots_used()}
GLOBAL BYTES USED: {self.global_bytes_used()}
GLOBAL UINTS USED: {self.global_uints_used()}
LOCAL BYTES USED: {self.local_bytes_used()}
LOCAL UINTS USED: {self.local_uints_used()}
        <<<<<<{self.name}>>>>>>"""

        txn_reports = []
        for i, txn in enumerate(self.resp["txns"]):
            txn_reports.append(
                self.txn_report(i, self.name, txn, self.col_max)
            )

        txn_reports = [bookend] + txn_reports + [bookend]

        return "\n".join(txn_reports)

    def txn_report(
        self, idx: int, run_name: str, txn: dict, col_max: int
    ) -> str:
        gdelta = txn.get("global-delta", [])
        ldelta = txn.get("local-deltas", [])

        app_messages = txn["app-call-messages"]
        app_trace = txn["app-call-trace"]
        cost = txn["cost"]
        app_lines = txn["disassembly"]

        lsig_lines = txn["logic-sig-disassembly"]
        lsig_messages = txn["logic-sig-messages"]
        lsig_trace = txn["logic-sig-trace"]

        app_table = trace_table(app_trace, app_lines, col_max)
        lsig_table = trace_table(lsig_trace, lsig_lines, col_max)

        return f"""===============
===============
TOTAL COST: {cost}
===============
txn.app_call_rejected={app_messages[-1] != 'PASS'}
txn.logic_sig_rejected={lsig_messages[-1] != 'PASS'}
===============
App Messages: {app_messages}
App Logs: {self.logs(idx)}
App Trace: (with max column size {col_max})
{app_table}
===============
Lsig Messages: {lsig_messages}
Lsig Trace: (with max column size {col_max})
{lsig_table}
===============
Global Delta:
{gdelta}
===============
Local Delta:
{ldelta}
"""


def do_dryrun(
    run_name: str,
    approval: ApprovalBundle,
    app_args: list,
    col_max: int = None,
):
    algod = get_algod()

    creator = get_creator()
    drc = DryRunContext(
        algod,
        creator,
    )

    with drc.application(
        approval.teal,
        local_schema=approval.local_schema,
        global_schema=approval.global_schema,
    ) as app:
        print(f"Created application {app.index} with address: {app.address}")

        app_txn = ApplicationCallTxn(
            creator.address,
            app.sp,
            app.index,
            OnComplete.NoOpOC,
            app_args=app_args,
        )
        sapp_txn = LogicSigTransaction(app_txn, drc.lsig_account)

        drr = create_dryrun(algod, [sapp_txn])
        resp = algod.dryrun(drr)
        print(
            DryRunTester(
                run_name, resp, creator.address, col_max=col_max
            ).report()
        )
