from algosdk import encoding
from algosdk import transaction
from algosdk import kmd
from algosdk import algod
from algosdk import crypto
from algosdk import mnemonic


# change these after starting the node and kmd
# algod info is in the algod.net and algod.token files in the node's data directory
# kmd info is in the kmd.net and kmd.token files in the kmd directory which is in data
kmdToken = "ddf94bd098816efcd2e47e12b5fe20285f48257201ca1fe4067000a15f3fbd69"
kmdAddress = "http://localhost:59987"
algodToken = "d05db6ecec87954e747bd66668ec6dd3c3cef86d99ea88e8ca42a20f93f6be01"
algodAddress = "http://localhost:61186"


# enter existing wallet and account info here
existing_wallet_name = "Wallet"
existing_wallet_pswd = ""
existing_account = "CCHVBXJ3YGYXZLRHAMTNYZ7OMTQX2PRUGP6NFQ5PBQISPLRSSTUF7JAMZY"


# new wallet to create
wallet_name = "example-wallet"
wallet_pswd = "example-password"

minTxnFee = 1000


# create kmd and algod clients
kcl = kmd.kmdClient(kmdToken, kmdAddress)
acl = algod.AlgodClient(algodToken, algodAddress)

# check if the wallet already exists
wallets = kcl.listWallets()
existing_wallet_id = None
wallet_id = None
for w in wallets:
    if w.name.__eq__(wallet_name):
        wallet_id = w.id
    elif w.name.__eq__(existing_wallet_name):
        existing_wallet_id = w.id

# if it doesn't exist, create the wallet and get its ID
if not wallet_id:
    wallet_id = kcl.createWallet(wallet_name, wallet_pswd).id
    print("Wallet ID: " + wallet_id)

# get a handle for the wallet
handle = kcl.initWalletHandle(wallet_id, wallet_pswd)
print("Wallet handle token: " + handle + "\n")

# generate account with crypto and check if it's valid
private_key_1, address_1 = crypto.generateAccount()
print("Private key: " + private_key_1 + "\n")
print("First account: " + address_1)

# import generated account into the wallet
kcl.importKey(handle, private_key_1)

# generate account with kmd
address_2 = kcl.generateKey(handle, False)
print("Second account: " + address_2 + "\n")

# get the mnemonic for address_1
mn = mnemonic.fromKey(address_1)
print("Mnemonic: " + mn + "\n")

# get suggested parameters
params = acl.suggestedParams()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]

# create a transaction
txn = transaction.PaymentTxn(existing_account, minTxnFee, last_round, last_round+100, gen, gh, address_1, 100000)
print("Encoded transaction:", encoding.msgpack_encode(txn), "\n")

# get a handle for the existing wallet
existing_handle = kcl.initWalletHandle(existing_wallet_id, existing_wallet_pswd)

# sign transaction with kmd
signed_kmd = kcl.signTransaction(existing_handle, existing_wallet_pswd, txn)

# get the private key for the existing account
private_key = kcl.exportKey(existing_handle, existing_wallet_pswd, existing_account)

# sign transaction with crypto
signed_crypto, txid, sig = crypto.signTransaction(txn, private_key)
print("Signature: " + signed_crypto.getSignature() + "\n")

# check that they're the same
if signed_crypto.dictify().__eq__(signed_kmd.dictify()):
    print("Signed transactions are the same!")
else:
    print("Well that's not good...")

# send the transaction
transaction_id = acl.sendRawTransaction(signed_kmd)
print("\nTransaction ID: " + transaction_id + "\n")

# Seeing the results: 
    # To see the new wallet and accounts that we've created, use goal:
    # $ ./goal wallet list
    # $ ./goal account list

# now write your own in main.py!

