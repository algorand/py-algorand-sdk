import base64
from algosdk import transaction
from utils import get_algod_client, get_accounts


accts = get_accounts()
creator = accts.pop()
user = accts.pop()

# example: APP_SCHEMA
local_ints = 1
local_bytes = 1
global_ints = 1
global_bytes = 1
local_schema = transaction.StateSchema(local_ints, local_bytes)
global_schema = transaction.StateSchema(global_ints, global_bytes)
# example: APP_SCHEMA

# example: APP_SOURCE
with open("calculator/approval.teal", "r") as f:
    approval_program = f.read()

with open("calculator/clear.teal", "r") as f:
    clear_program = f.read()
# example: APP_SOURCE

algod_client = get_algod_client()
# example: APP_COMPILE
approval_result = algod_client.compile(approval_program)
approval_binary = base64.b64decode(approval_result["result"])

clear_result = algod_client.compile(clear_program)
clear_binary = base64.b64decode(clear_result["result"])
# example: APP_COMPILE

# example: APP_CREATE
sp = algod_client.suggested_params()
# create the app create transaction, passing compiled programs and schema
app_create_txn = transaction.ApplicationCreateTxn(
    creator.address,
    sp,
    transaction.OnComplete.NoOpOC,
    approval_program=approval_binary,
    clear_program=clear_binary,
    global_schema=global_schema,
    local_schema=local_schema,
)
# sign transaction
signed_create_txn = app_create_txn.sign(creator.private_key)
txid = algod_client.send_transaction(signed_create_txn)
result = transaction.wait_for_confirmation(algod_client, txid, 4)
app_id = result['application-index']
print(f"Created app with id: {app_id}")
# example: APP_CREATE

# example: APP_OPTIN
opt_in_txn = transaction.ApplicationOptInTxn(user.address, sp, app_id)
signed_opt_in = opt_in_txn.sign(user.private_key)
txid = algod_client.send_transaction(signed_opt_in)
transaction.wait_for_confirmation(algod_client, txid, 4)
# example: APP_OPTIN

# example: APP_NOOP
#opt_in_txn = transaction.ApplicationOptInTxn(user.address, sp, app_id)
#signed_opt_in = opt_in_txn.sign(user.private_key)
#txid = algod_client.send_transaction(signed_create_txn)
#transaction.wait_for_confirmation(algod_client, txid, 4)
# example: APP_NOOP

# example: APP_READ_STATE
acct_info = algod_client.account_info(user.address)
print(acct_info)
# example: APP_READ_STATE

# example: APP_UPDATE
# example: APP_UPDATE

# example: APP_CALL
# example: APP_CALL

# example: APP_CLOSEOUT
# example: APP_CLOSEOUT

# example: APP_DELETE
# example: APP_DELETE

# example: APP_CLEAR
# example: APP_CLEAR
