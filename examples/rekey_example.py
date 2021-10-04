# Example: rekeying

from algosdk import account, algod
from algosdk.future import transaction
import tokens

# this should be the current account
sender_private_key, sender = account.generate_account()
rekey_private_key, rekey_address = account.generate_account()
receiver = sender
amount = 0

# get suggested parameters
acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)
suggested_params = acl.suggested_params_as_object()

# To rekey an account to a new address, add the `rekey_to` argument to creation.
# After sending this rekeying transaction, every transaction needs to be signed by the private key of the new address
rekeying_txn = transaction.PaymentTxn(
    sender, suggested_params, receiver, amount, rekey_to=rekey_address
)
