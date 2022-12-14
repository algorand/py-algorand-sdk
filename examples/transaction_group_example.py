# Example: working with transaction groups

import tokens

from algosdk import account, kmd, transaction
from algosdk.v2client import algod

# generate accounts
private_key_sender, sender = account.generate_account()
private_key_receiver, receiver = account.generate_account()

# create an algod and kmd client
acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)
kcl = kmd.KMDClient(tokens.kmd_token, tokens.kmd_address)

# get suggested parameters
sp = acl.suggested_params()

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

# send them over network (note that the accounts need to be funded for this to work)
acl.send_transactions([stxn1, stxn2])
