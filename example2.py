from algosdk import encoding
from algosdk import transaction
from algosdk import kmd
from algosdk import algod
from algosdk import crypto
from algosdk import mnemonic
from algosdk import constants
from algosdk import wallet
import params

# create kmd and algod clients
kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)
acl = algod.AlgodClient(params.algodToken, params.algodAddress)

# enter existing wallet and account info here
existing_wallet_name = input("Existing wallet name? ")
existing_wallet_pswd = input("Existing wallet password? ")
existing_account = input("Address of an account in the wallet? ")

w = wallet.Wallet(existing_wallet_name, existing_wallet_pswd, kcl)

# new wallet to create
print("Now we'll create a new wallet.")
wallet_name = input("New wallet name? ")
wallet_pswd = input("New wallet password? ")

new_wallet = wallet.Wallet(wallet_name, wallet_pswd, kcl)

# generate account with crypto and check if it's valid
private_key_1, address_1 = crypto.generateAccount()
print("Private key: " + private_key_1 + "\n")
print("First account: " + address_1)

# import generated account into the wallet
new_wallet.importKey(private_key_1)

# generate account with kmd
address_2 = new_wallet.generateKey()
print("Second account: " + address_2 + "\n")

# get the mnemonic for address_1
mn = mnemonic.fromPrivateKey(private_key_1)
print("Mnemonic for the first account: " + mn + "\n")

# get suggested parameters
params = acl.suggestedParams()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]

# create a transaction
txn = transaction.PaymentTxn(existing_account, constants.minTxnFee, last_round, last_round+100, gen, gh, address_1, 100000)
print("Encoded transaction:", encoding.msgpack_encode(txn), "\n")

# sign transaction with kmd
signed_kmd = w.signTransaction(txn)

# get the private key for the existing account
private_key = w.exportKey(existing_account)

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
print("\nTransaction was sent!")
print("Transaction ID: " + transaction_id + "\n")

# Seeing the results: 
    # To see the new wallet and accounts that we've created, use goal:
    # $ ./goal wallet list
    # $ ./goal account list

# now write your own in main.py!

