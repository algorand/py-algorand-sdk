from typing import Dict, Any
import json
from base64 import b64decode
from utils import get_accounts

from algosdk import transaction
from algosdk.v2client import algod


# example: CREATE_ALGOD_CLIENT
# Create a new algod client, configured to connect to our local sandbox
algod_address = "http://localhost:4001"
algod_token = "a" * 64
algod_client = algod.AlgodClient(algod_token, algod_address)

# Or, if necessary, pass alternate headers

# Create a new client with an alternate api key header
special_algod_client = algod.AlgodClient(
    "", algod_address, headers={"X-API-Key": algod_token}
)
# example: CREATE_ALGOD_CLIENT

accts = get_accounts()

acct1 = accts.pop()
private_key, address = acct1.private_key, acct1.address

acct2 = accts.pop()
address2 = acct2.address

# example: FETCH_ACCOUNT_INFO
account_info: Dict[str, Any] = algod_client.account_info(address)
print(f"Account balance: {account_info.get('amount')} microAlgos")
# example: FETCH_ACCOUNT_INFO


# example: SIMPLE_PAYMENT_TRANSACTION_CREATE
# grab suggested params from algod using client
# includes things like suggested fee and first/last valid rounds
params = algod_client.suggested_params()
unsigned_txn = transaction.PaymentTxn(
    sender=address,
    sp=params,
    receiver=address2,
    amt=1000000,
    note=b"Hello World",
)
# example: SIMPLE_PAYMENT_TRANSACTION_CREATE

# example: SIMPLE_PAYMENT_TRANSACTION_SIGN
# sign the transaction
signed_txn = unsigned_txn.sign(private_key)
# example: SIMPLE_PAYMENT_TRANSACTION_SIGN

# example: SIMPLE_PAYMENT_TRANSACTION_SUBMIT
# submit the transaction and get back a transaction id
txid = algod_client.send_transaction(signed_txn)
print("Successfully submitted transaction with txID: {}".format(txid))

# wait for confirmation
txn_result = transaction.wait_for_confirmation(algod_client, txid, 4)

print(f"Transaction information: {json.dumps(txn_result, indent=4)}")
print(f"Decoded note: {b64decode(txn_result['txn']['txn']['note'])}")
# example: SIMPLE_PAYMENT_TRANSACTION_SUBMIT
