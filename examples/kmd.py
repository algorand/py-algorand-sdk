from algosdk import kmd, wallet, mnemonic, account
from utils import get_kmd_client


# example: KMD_CREATE_CLIENT
kmd_address = "http://localhost:4002"
kmd_token = "a" * 64

kmd_client = kmd.KMDClient(kmd_token=kmd_token, kmd_address=kmd_address)
# example: KMD_CREATE_CLIENT

kmd_client = get_kmd_client()


def get_wallet_id_from_name(name: str):
    wallets = kmd_client.list_wallets()
    wallet_id = None
    for w in wallets:
        if w["name"] == name:
            wallet_id = w["id"]
            break

    if wallet_id is None:
        raise Exception(f"No wallet with name {name} found")

    return wallet_id


# example: KMD_CREATE_WALLET
# create a wallet object which, if not available yet, also creates the wallet in the KMD
wlt = wallet.Wallet("MyNewWallet", "supersecretpassword", kmd_client)
# get wallet information
info = wlt.info()
print(f"Wallet name: {info['wallet']['name']}")

backup = wlt.get_mnemonic()
print(f"mnemonic for master derivation key: {backup}")
# example: KMD_CREATE_WALLET

# example: KMD_CREATE_ACCOUNT
# create an account using the wallet object
address = wlt.generate_key()
print(f"New account: {address}")
# example: KMD_CREATE_ACCOUNT


# example: KMD_RECOVER_WALLET
# Create the master derivation key from our backed up mnemonic
mdk = mnemonic.to_master_derivation_key(backup)

# recover the wallet by passing mdk during creation
new_wallet = wallet.Wallet(
    "MyNewWalletCopy", "testpassword", kmd_client, mdk=mdk
)

info = new_wallet.info()
wallet_id = info["wallet"]["id"]
print(f"Created Wallet: {wallet_id}")

rec_addr = wlt.generate_key()
print("Recovered account:", rec_addr)
# example: KMD_RECOVER_WALLET

# example: KMD_EXPORT_ACCOUNT
# Get the id for the wallet we want to export an account from
wallet_id = get_wallet_id_from_name("MyNewWallet")
# Get a session handle for the wallet after providing password
wallethandle = kmd_client.init_wallet_handle(wallet_id, "supersecretpassword")
# Export the account key for the address passed
accountkey = kmd_client.export_key(
    wallethandle, "supersecretpassword", address
)
# Print the mnemonic for the accounts private key
mn = mnemonic.from_private_key(accountkey)
print(f"Account mnemonic: {mn}")
# example: KMD_EXPORT_ACCOUNT

# example: KMD_IMPORT_ACCOUNT
wallet_id = get_wallet_id_from_name("MyNewWallet")

# Generate a new account client side
new_private_key, new_address = account.generate_account()
mn = mnemonic.from_private_key(new_private_key)
print(f"Account: {new_address} Mnemonic: {mn}")

# Import the account to the wallet in KMD
wallethandle = kmd_client.init_wallet_handle(wallet_id, "supersecretpassword")
importedaccount = kmd_client.import_key(wallethandle, new_private_key)
print("Account successfully imported: ", importedaccount)
# example: KMD_IMPORT_ACCOUNT
