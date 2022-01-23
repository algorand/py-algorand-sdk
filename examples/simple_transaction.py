from pyteal import *
from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk.future import transaction

mnemonic1 = "PASTE-THROWAWAY-MNEMONIC-HERE"

public_key = mnemonic.to_public_key(mnemonic1)
secret_key = mnemonic.to_private_key(mnemonic1)

algod_address = "PASTE-ALGOD-ADDRESS"
algod_token = "PASTE-TOKEN-ADDRESS"

algod_client = algod.AlgodClient(algod_token = algod_token, algod_address = algod_address)

alice = "PASTE-RECEIVING-ADDRESS-HERE"

def simple_transaction():

    print("Making a transaction.")
    params = algod_client.suggested_params()
    receiver = alice
    amount = 1000000 # 1 Algo = 1000000 mAlgos

    print("Compiling transaction.")
    unsigned_txn = transaction.PaymentTxn(public_key, params, receiver, amount)

    print("Signing transaction.")
    signed_txn = unsigned_txn.sign(secret_key)

    txid = algod_client.send_transaction(signed_txn)
    print("Transaction ID: {}".format(txid))

simple_transaction()