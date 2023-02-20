from dataclasses import dataclass

from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.kmd import KMDClient
from algosdk.wallet import Wallet

DEFAULT_KMD_ADDRESS = "http://localhost:4002"
DEFAULT_KMD_TOKEN = "a" * 64
DEFAULT_KMD_WALLET_NAME = "unencrypted-default-wallet"
DEFAULT_KMD_WALLET_PASSWORD = ""


def get_client() -> KMDClient:
    """creates a new kmd client using the default sandbox parameters"""
    return KMDClient(
        kmd_token=DEFAULT_KMD_TOKEN, kmd_address=DEFAULT_KMD_ADDRESS
    )


def get_sandbox_default_wallet() -> Wallet:
    """returns the default sandbox kmd wallet"""
    return Wallet(
        wallet_name=DEFAULT_KMD_WALLET_NAME,
        wallet_pswd=DEFAULT_KMD_WALLET_PASSWORD,
        kmd_client=get_client(),
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


def get_accounts(
    kmd_address: str = DEFAULT_KMD_ADDRESS,
    kmd_token: str = DEFAULT_KMD_TOKEN,
    wallet_name: str = DEFAULT_KMD_WALLET_NAME,
    wallet_password: str = DEFAULT_KMD_WALLET_PASSWORD,
) -> list[SandboxAccount]:
    """gets all the accounts in the sandbox kmd, defaults
    to the `unencrypted-default-wallet` created on private networks automatically"""

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
