# Example: logic sig for a rekeyed account

from algosdk import account, algod
from algosdk.future import transaction
import tokens

sender = "FDZDQXYY2HLHBWAYRXSRSEIXRDDN4D7DV76U4RRUESK2ONSQHTGHS2NO6Q"
rekey_address = "YOE6C22GHCTKAN3HU4SE5PGIPN5UKXAJTXCQUPJ3KKF5HOAH646MKKCPDA"
program = b'\x02 \x01\x01"'
lsig = transaction.LogicSig(program)
# assume that the `sender` above is rekeyed to `rekey_address` that
# is the contract account address for the TEAL script `program`:
#   #pragma version 2
#   int 1
# (this is the case on TestNet at round 12171570)
receiver = sender
amount = 1

# get suggested parameters
acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)
suggested_params = acl.suggested_params_as_object()

# create a transaction
txn = transaction.PaymentTxn(sender, suggested_params, receiver, amount)

# transaction is signed by logic only (no delegation)
# but the sender is rekeyed
lstx = transaction.LogicSigTransaction(txn, lsig, rekey_address)
assert lstx.verify()

# send them over network
acl.send_transaction(lstx)