from base64 import b64decode
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, List

from algosdk.v2client.algod import AlgodClient
from algosdk.dryrun_results import DryrunResponse, DryrunTransactionResult
from algosdk.future.transaction import (
    ApplicationCallTxn,
    ApplicationCreateTxn,
    ApplicationDeleteTxn,
    LogicSigAccount,
    LogicSigTransaction,
    OnComplete,
    # PaymentTxn,
    SignedTransaction,
    StateSchema,
    SuggestedParams,
    # assign_group_id,
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
            sp = self.algod.suggested_params()

            app_delete = ApplicationDeleteTxn(self.creator.address, sp, app_id)
            signed_delete = app_delete.sign(self.creator.secret)
            txid = self.algod.send_transaction(signed_delete)
            print(f"Gonna delete app with index={app_id}")
            addr = self.creator.address
            created_apps = self.algod.account_info(addr)["created-apps"]
            print(
                f"""Before commencing, creator [{addr}] currently has {len(created_apps)} live apps
These have indices: {', '.join(str(a['id']) for a in created_apps)}"""
            )


def cleanup():
    print("\n\n\n --------- TEARDOWN --------- \n\n")
    creator = get_creator()
    addr = creator.address
    pk = creator.secret
    algod = get_algod()
    sp = algod.suggested_params()
    created_apps = algod.account_info(addr)["created-apps"]
    print(
        f"""Gonna tear down {len(created_apps)} apps for account {addr}
These have indexes: {','.join(str(a['id']) for a in created_apps)}"""
    )
    for app in created_apps:
        index = app["id"]
        app_delete = ApplicationDeleteTxn(addr, sp, index)
        signed_delete = app_delete.sign(pk)
        algod.send_transaction(signed_delete)


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


def dryrun_report(i: int, run_name: str, txn: DryrunTransactionResult) -> str:
    return f"""===============
{i}. <<<{run_name}>>>
===============
txn.app_call_rejected={txn.app_call_rejected()}
txn.logic_sig_rejected={txn.logic_sig_rejected()}
===============
App Messages: {txn.app_call_messages}
App Logs: {txn.logs}
App Trace:
{txn.app_trace(0)}
===============
Lsig Messages: {txn.logic_sig_messages}
Lsig Trace: 
{txn.lsig_trace(0)}
"""


@dataclass
class ApprovalBundle:
    teal: str
    local_schema: StateSchema = ZERO_SCHEMA
    global_schema: StateSchema = ZERO_SCHEMA


def do_dryrun(
    run_name: str,
    approval: ApprovalBundle,
    *app_args: Any,
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

        sig_addr = drc.lsig_account.address()
        print(f"Created Signature with address: {sig_addr}")

        # pay_txn = PaymentTxn(creator.address, app.sp, sig_addr, 10000)
        app_txn = ApplicationCallTxn(
            # sig_addr,
            creator.address,
            app.sp,
            app.index,
            OnComplete.NoOpOC,
            app_args=app_args,
        )
        # assign_group_id([pay_txn, app_txn])
        # spay_txn = pay_txn.sign(creator.secret)
        sapp_txn = LogicSigTransaction(app_txn, drc.lsig_account)

        # drr = create_dryrun(algod, [spay_txn, sapp_txn])

        drr = create_dryrun(algod, [sapp_txn])
        raw = algod.dryrun(drr)
        resp = DryrunResponse(raw)
        for i, txn in enumerate(resp.txns):
            print(dryrun_report(i + 1, run_name, txn))
