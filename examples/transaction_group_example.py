
# Example: working with transaction group

import params
from algosdk import algod, kmd, account
from algosdk.future import transaction

private_key_sender, sender = account.generate_account()
private_key_receiver, receiver = account.generate_account()

# create an algod and kmd client
acl = algod.AlgodClient(params.algod_token, params.algod_address)
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# get suggested parameters
sp = acl.suggested_params_as_object()

# create a transaction
amount = 10000
txn1 = transaction.PaymentTxn(sender, sp, receiver, amount)
txn2 = transaction.PaymentTxn(receiver, sp, sender, amount)

# get group id and assign it to transactions
gid = transaction.calculate_group_id([txn1, txn2])
txn1.group = gid
txn2.group = gid

# sign transactions
stxn1 = txn1.sign(private_key_sender)
stxn2 = txn2.sign(private_key_receiver)

# send them over network
acl.send_transactions([stxn1, stxn2])
