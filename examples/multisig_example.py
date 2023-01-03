# Example: manipulating multisig transactions

import tokens

from algosdk import account, encoding, transaction
from algosdk.v2client import algod

# generate three accounts
private_key_1, account_1 = account.generate_account()
private_key_2, account_2 = account.generate_account()
private_key_3, account_3 = account.generate_account()

# create a multisig account
version = 1  # multisig version
threshold = 2  # how many signatures are necessary
msig = transaction.Multisig(version, threshold, [account_1, account_2])

# get suggested parameters
acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)
suggested_params = acl.suggested_params()

# create a transaction
sender = msig.address()
amount = 10000
txn = transaction.PaymentTxn(sender, suggested_params, account_3, amount)

# create a SignedTransaction object
mtx = transaction.MultisigTransaction(txn, msig)

# sign the transaction
mtx.sign(private_key_1)
mtx.sign(private_key_2)

# print encoded transaction
print("Encoded transaction:", encoding.msgpack_encode(mtx))
