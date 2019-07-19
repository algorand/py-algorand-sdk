from algosdk import encoding
from algosdk import transaction
from algosdk import kmd
from algosdk import algod
from algosdk import account
from algosdk import mnemonic
import params
import json

# create kmd and algod clients
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)
acl = algod.AlgodClient(params.algod_token, params.algod_address)

# enter existing wallet and account info here
existing_wallet_name = input("Name of an existing wallet? ")
existing_wallet_pswd = input("Password for " + existing_wallet_name + "? ")
existing_account = input("Address of an account in the wallet? ")

# or enter info here
# existing_wallet_name = "unencrypted-default-wallet"
# existing_wallet_pswd = ""
# existing_account = "account_address"

# get the wallet ID
wallets = kcl.list_wallets()
existing_wallet_id = None
for w in wallets:
    if w["name"] == existing_wallet_name:
        existing_wallet_id = w["id"]
        break

# get a handle for the existing wallet
existing_handle = kcl.init_wallet_handle(existing_wallet_id,
                                         existing_wallet_pswd)
print("Got the wallet's handle: " + existing_handle)

# new wallet to create
print("Now we'll create a new wallet.")
wallet_name = input("New wallet name? ")
wallet_pswd = input("New wallet password? ")

# or enter wallet info here
# wallet_name = "Wallet"
# wallet_pswd = "password"

# check if the wallet already exists
wallet_id = None
for w in wallets:
    if w["name"] == wallet_name:
        wallet_id = w["id"]
        print("The wallet already exists, but let's just go with it!")
        break

# if it doesn't exist, create the wallet and get its ID
if not wallet_id:
    wallet_id = kcl.create_wallet(wallet_name, wallet_pswd)["id"]
    print("Wallet created!")
    print("Wallet ID: " + wallet_id)

# get a handle for the wallet
handle = kcl.init_wallet_handle(wallet_id, wallet_pswd)
print("Wallet handle token: " + handle + "\n")

# generate account with account and check if it's valid
private_key_1, address_1 = account.generate_account()
print("Private key: " + private_key_1 + "\n")
print("First account: " + address_1)

# import generated account into the wallet
kcl.import_key(handle, private_key_1)

# generate account with kmd
address_2 = kcl.generate_key(handle, False)
print("Second account: " + address_2 + "\n")

# get the mnemonic for address_1
mn = mnemonic.from_private_key(private_key_1)
print("Mnemonic for the first account: " + mn + "\n")

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]
fee = params["fee"]

# get last block info
block_info = acl.block_info(last_round)
print("Block", last_round, "info:", json.dumps(block_info, indent=2), "\n")

# create a transaction
amount = 100000
txn = transaction.PaymentTxn(existing_account, fee, last_round,
                             last_round+100, gh, address_1, amount, gen=gen)
print("Encoded transaction:", encoding.msgpack_encode(txn), "\n")

# sign transaction with kmd
signed_kmd = kcl.sign_transaction(existing_handle, existing_wallet_pswd, txn)

# get the private key for the existing account
private_key = kcl.export_key(existing_handle, existing_wallet_pswd,
                             existing_account)

# sign transaction with account
signed_account = txn.sign(private_key)
print("Signature: " + signed_account.signature + "\n")

# check that they're the same
if signed_account.dictify() == signed_kmd.dictify():
    print("Signed transactions are the same!")
else:
    print("Well that's not good...")

# send the transaction
transaction_id = acl.send_raw_transaction(signed_kmd)
print("\nTransaction was sent!")
print("Transaction ID: " + transaction_id + "\n")

# wait 2 rounds and then try to see the transaction
print("Now let's wait a bit for the transaction to process.\n")
acl.status_after_block(last_round+2)
print("Transaction info:", acl.transaction_info(existing_account,
                                                transaction_id))

# To see the new wallet and accounts that we've created, use goal:
# $ ./goal wallet list
# $ ./goal account list

# now write your own!
