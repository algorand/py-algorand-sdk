"""
Interface between the black box analysis and the sand box runtime
"""
from base64 import b64decode
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator, List, Union

from algosdk.future.transaction import (
    LogicSigTransaction,
    ApplicationClearStateTxn,
    ApplicationCreateTxn,
    ApplicationOptInTxn,
    ApplicationDeleteTxn,
    LogicSigAccount,
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
from algosdk.v2client.algod import AlgodClient

SB_ALGOD_ADDRESS = "http://localhost:4001"
SB_ALGOD_TOKEN = "a" * 64

SB_KMD_ADDRESS = "http://localhost:4002"
SB_KMD_TOKEN = "a" * 64

SB_KMD_WALLET_NAME = "unencrypted-default-wallet"
SB_KMD_WALLET_PASSWORD = ""

CLEAR_TEAL = """{}
pushint 1
return"""

LOGIC_SIG_TEAL = """{}
pushint 1"""


ZERO_SCHEMA = StateSchema(num_uints=0, num_byte_slices=0)


@dataclass
class AddressAndSecret:
    address: str
    secret: str


@dataclass
class ApplicationBundle:
    author: "AddressAndSecret"
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


class DryRunContext:
    def __init__(
        self,
        algod: AlgodClient = None,
        creator: "AddressAndSecret" = None,
        clear_src: str = CLEAR_TEAL,
        lsig_src: str = LOGIC_SIG_TEAL,
    ):
        if not algod:
            algod = get_algod()
        if not creator:
            creator = get_creator()

        self.algod = algod
        self.creator = creator
        self.clear_src_tmpl = clear_src

        self.lsig_src_tmpl = lsig_src
        self.lsig_src: str
        self.lsig: bytes
        self.lsig_account: LogicSigAccount

    def dryrun(
        self, l_or_s_txns: List[Union[SignedTransaction, LogicSigTransaction]]
    ) -> dict:
        drr = create_dryrun(self.algod, l_or_s_txns)
        resp = self.algod.dryrun(drr)
        return resp

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

        # Create and simultaneously opt-in to the app just created:
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
