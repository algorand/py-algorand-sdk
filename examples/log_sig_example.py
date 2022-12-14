# Example: creating a LogicSig transaction signed by a program that never approves the transfer.

import tokens
from algosdk import account, transaction
from algosdk.v2client import algod

program = b"\x01\x20\x01\x00\x22"  # int 0
lsig = transaction.LogicSigAccount(program)
sender = lsig.address()
_, receiver = account.generate_account()

# create an algod client
acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)

# get suggested parameters
sp = acl.suggested_params()

# create a transaction
amount = 10000
txn = transaction.PaymentTxn(sender, sp, receiver, amount)

# note: transaction is signed by logic only (no delegation)
# that means sender address must match to program hash
lstx = transaction.LogicSigTransaction(txn, lsig)
assert lstx.verify()

# send them over network
# Logicsig will reject the transaction
acl.send_transaction(lstx)
