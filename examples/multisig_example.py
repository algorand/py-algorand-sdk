
# Example: manipulating multisig transactions

import params
from algosdk import account, algod, encoding
from algosdk.future import transaction

# generate three accounts
private_key_1, account_1 = account.generate_account()
private_key_2, account_2 = account.generate_account()
private_key_3, account_3 = account.generate_account()

# create a multisig account
version = 1  # multisig version
threshold = 2  # how many signatures are necessary
msig = transaction.Multisig(version, threshold, [account_1, account_2])

# get suggested parameters
acl = algod.AlgodClient(params.algod_token, params.algod_address)
sp = acl.suggested_params_as_object()

# create a transaction
sender = msig.address()
amount = 10000
txn = transaction.PaymentTxn(sender, sp, account_3, amount)

# create a SignedTransaction object
mtx = transaction.MultisigTransaction(txn, msig)

# sign the transaction
mtx.sign(private_key_1)
mtx.sign(private_key_2)

# print encoded transaction
print(encoding.msgpack_encode(mtx))
