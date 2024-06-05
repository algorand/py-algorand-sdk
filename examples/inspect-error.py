from algosdk import error, transaction

from utils import get_algod_client, algod_env

algod = get_algod_client(*algod_env())

# This program is "#pragma version 5, +". It will fail because no arguments are on the stack.
lsig = transaction.LogicSigAccount(b"\x05\x08")
sender = lsig.address()
# Get suggested parameters
params = algod.suggested_params()

amount = 10000
txn = transaction.PaymentTxn(sender, params, sender, amount)
lstx = transaction.LogicSigTransaction(txn, lsig)
try:
    txid = algod.send_transaction(lstx)
    print("Impossible! Exception will have been thrown")
except error.AlgodHTTPError as e:
    print(e.data)
