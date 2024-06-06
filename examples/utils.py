import os
import base64
import time
from dataclasses import dataclass
from typing import List

from algosdk import transaction
from algosdk.v2client import algod, indexer
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.kmd import KMDClient
from algosdk.wallet import Wallet

KMD_ADDRESS = "http://localhost"
KMD_TOKEN = "a" * 64
KMD_PORT = os.getenv("KMD_PORT", default="4002")
KMD_URL = f"{KMD_ADDRESS}:{KMD_PORT}"

DEFAULT_KMD_WALLET_NAME = "unencrypted-default-wallet"
DEFAULT_KMD_WALLET_PASSWORD = ""

ALGOD_ADDRESS = "http://localhost"
ALGOD_TOKEN = "a" * 64
ALGOD_PORT = os.getenv("ALGOD_PORT", default="4001")
ALGOD_URL = f"{ALGOD_ADDRESS}:{ALGOD_PORT}"

INDEXER_ADDRESS = "http://localhost"
INDEXER_TOKEN = "a" * 64
INDEXER_PORT = os.getenv("INDEXER_PORT", default="8980")
INDEXER_URL = f"{INDEXER_ADDRESS}:{INDEXER_PORT}"


def get_algod_client(
    addr: str = ALGOD_URL, token: str = ALGOD_TOKEN
) -> algod.AlgodClient:
    return algod.AlgodClient(algod_token=token, algod_address=addr)


def get_kmd_client(addr: str = KMD_URL, token: str = KMD_TOKEN) -> KMDClient:
    """creates a new kmd client using the default sandbox parameters"""
    return KMDClient(kmd_token=token, kmd_address=addr)


def get_indexer_client(
    addr: str = INDEXER_URL, token: str = INDEXER_TOKEN
) -> indexer.IndexerClient:
    """creates a new indexer client using the default sandbox parameters"""
    return indexer.IndexerClient(indexer_token=token, indexer_address=addr)


def get_sandbox_default_wallet() -> Wallet:
    """returns the default sandbox kmd wallet"""
    return Wallet(
        wallet_name=DEFAULT_KMD_WALLET_NAME,
        wallet_pswd=DEFAULT_KMD_WALLET_PASSWORD,
        kmd_client=get_kmd_client(),
    )


def indexer_wait_for_round(
    client: indexer.IndexerClient, round: int, max_attempts: int
) -> None:
    """waits for the indexer to catch up to the given round"""
    indexer_round = 0
    attempts = 0

    while True:
        indexer_status = client.health()
        indexer_round = indexer_status["round"]
        if indexer_round >= round:
            # Success
            break

        # Sleep for 1 second and try again
        time.sleep(1)
        attempts += 1

        if attempts >= max_attempts:
            # Failsafe to prevent infinite loop
            raise RuntimeError(
                f"Timeout waiting for indexer to catch up to round {round}. It is currently on {indexer_round}"
            )


@dataclass
class SandboxAccount:
    """SandboxAccount is a simple dataclass to hold a sandbox account details"""

    #: The address of a sandbox account
    address: str
    #: The base64 encoded private key of the account
    private_key: str
    #: An AccountTransactionSigner that can be used as a TransactionSigner
    signer: AccountTransactionSigner


def algod_env():
    algodata = os.environ.get("ALGORAND_DATA")
    if not algodata:
        return ()
    try:
        token = (
            open(os.path.join(algodata, "algod.token"), "rt").read().strip()
        )
        net = (
            "http://"
            + open(os.path.join(algodata, "algod.net"), "rt").read().strip()
        )
        return (net, token)
    except FileNotFoundError:
        return ()


def get_accounts(
    kmd_address: str = KMD_URL,
    kmd_token: str = KMD_TOKEN,
    wallet_name: str = DEFAULT_KMD_WALLET_NAME,
    wallet_password: str = DEFAULT_KMD_WALLET_PASSWORD,
) -> List[SandboxAccount]:
    """gets all the accounts in the sandbox kmd, defaults
    to the `unencrypted-default-wallet` created on private networks automatically
    """

    kmd = KMDClient(kmd_token, kmd_address)
    wallets = kmd.list_wallets()

    wallet_id = None
    for wallet in wallets:
        if wallet["name"] == wallet_name:
            wallet_id = wallet["id"]
            break

    if wallet_id is None:
        raise Exception("Wallet not found: {}".format(wallet_name))

    wallet_handle = kmd.init_wallet_handle(wallet_id, wallet_password)

    try:
        addresses = kmd.list_keys(wallet_handle)
        private_keys = [
            kmd.export_key(wallet_handle, wallet_password, addr)
            for addr in addresses
        ]
        kmd_accounts = [
            SandboxAccount(
                addresses[i],
                private_keys[i],
                AccountTransactionSigner(private_keys[i]),
            )
            for i in range(len(private_keys))
        ]
    finally:
        kmd.release_wallet_handle(wallet_handle)

    return kmd_accounts


def deploy_calculator_app(
    algod_client: algod.AlgodClient, acct: SandboxAccount
) -> int:
    with open("calculator/approval.teal", "r") as f:
        approval_program = f.read()

    with open("calculator/clear.teal", "r") as f:
        clear_program = f.read()

    approval_result = algod_client.compile(approval_program)
    approval_binary = base64.b64decode(approval_result["result"])

    clear_result = algod_client.compile(clear_program)
    clear_binary = base64.b64decode(clear_result["result"])

    sp = algod_client.suggested_params()
    # create the app create transaction, passing compiled programs and schema
    app_create_txn = transaction.ApplicationCreateTxn(
        acct.address,
        sp,
        transaction.OnComplete.NoOpOC,
        approval_program=approval_binary,
        clear_program=clear_binary,
        local_schema=transaction.StateSchema(num_uints=1, num_byte_slices=1),
        global_schema=transaction.StateSchema(num_uints=1, num_byte_slices=1),
    )
    # sign transaction
    signed_create_txn = app_create_txn.sign(acct.private_key)
    txid = algod_client.send_transaction(signed_create_txn)
    result = transaction.wait_for_confirmation(algod_client, txid, 4)
    app_id = result["application-index"]
    return app_id
