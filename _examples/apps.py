import base64
import datetime
from algosdk import transaction
from utils import get_algod_client, get_accounts


accts = get_accounts()
creator = accts.pop()
user = accts.pop()

# example: APP_SCHEMA
# create schema for both global and local state, specifying
# how many keys of each type we need to have available
local_schema = transaction.StateSchema(num_uints=1, num_byte_slices=1)
global_schema = transaction.StateSchema(num_uints=1, num_byte_slices=1)
# example: APP_SCHEMA

# example: APP_SOURCE
# read the `.teal` source files from disk
with open("application/approval.teal", "r") as f:
    approval_program = f.read()

with open("application/clear.teal", "r") as f:
    clear_program = f.read()
# example: APP_SOURCE

algod_client = get_algod_client()

# example: APP_COMPILE
# pass the `.teal` files to the compile endpoint
# and b64 decode the result to bytes
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
app_id = result["application-index"]
print(f"Created app with id: {app_id}")
# example: APP_CREATE

# example: APP_OPTIN
opt_in_txn = transaction.ApplicationOptInTxn(user.address, sp, app_id)
signed_opt_in = opt_in_txn.sign(user.private_key)
txid = algod_client.send_transaction(signed_opt_in)
optin_result = transaction.wait_for_confirmation(algod_client, txid, 4)
assert optin_result["confirmed-round"] > 0
# example: APP_OPTIN

# example: APP_NOOP
noop_txn = transaction.ApplicationNoOpTxn(user.address, sp, app_id)
signed_noop = noop_txn.sign(user.private_key)
txid = algod_client.send_transaction(signed_noop)
noop_result = transaction.wait_for_confirmation(algod_client, txid, 4)
assert noop_result["confirmed-round"] > 0
# example: APP_NOOP

# example: APP_READ_STATE
acct_info = algod_client.account_application_info(user.address, app_id)
# base64 encoded keys and values
print(acct_info["app-local-state"]["key-value"])
# example: APP_READ_STATE

# example: APP_UPDATE
with open("application/approval_refactored.teal", "r") as f:
    approval_program = f.read()

approval_result = algod_client.compile(approval_program)
approval_binary = base64.b64decode(approval_result["result"])


sp = algod_client.suggested_params()
# create the app update transaction, passing compiled programs and schema
# note that schema is immutable, we cant change it after create
app_update_txn = transaction.ApplicationUpdateTxn(
    creator.address,
    sp,
    app_id,
    approval_program=approval_binary,
    clear_program=clear_binary,
)
signed_update = app_update_txn.sign(creator.private_key)
txid = algod_client.send_transaction(signed_update)
update_result = transaction.wait_for_confirmation(algod_client, txid, 4)
assert update_result["confirmed-round"] > 0
# example: APP_UPDATE

# example: APP_CALL
now = datetime.datetime.now().strftime("%H:%M:%S")
app_args = [now.encode("utf-8")]
call_txn = transaction.ApplicationNoOpTxn(user.address, sp, app_id, app_args)

signed_call = call_txn.sign(user.private_key)
txid = algod_client.send_transaction(signed_call)
call_result = transaction.wait_for_confirmation(algod_client, txid, 4)
assert call_result["confirmed-round"] > 0

# display results
print("Called app-id: ", call_result["txn"]["txn"]["apid"])
if "global-state-delta" in call_result:
    print("Global State updated :\n", call_result["global-state-delta"])
if "local-state-delta" in call_result:
    print("Local State updated :\n", call_result["local-state-delta"])
# example: APP_CALL

# example: APP_CLOSEOUT
close_txn = transaction.ApplicationCloseOutTxn(user.address, sp, app_id)
signed_close = close_txn.sign(user.private_key)
txid = algod_client.send_transaction(signed_close)
optin_result = transaction.wait_for_confirmation(algod_client, txid, 4)
assert optin_result["confirmed-round"] > 0
# example: APP_CLOSEOUT

# example: APP_DELETE
delete_txn = transaction.ApplicationDeleteTxn(creator.address, sp, app_id)
signed_delete = delete_txn.sign(creator.private_key)
txid = algod_client.send_transaction(signed_delete)
optin_result = transaction.wait_for_confirmation(algod_client, txid, 4)
assert optin_result["confirmed-round"] > 0
# example: APP_DELETE

# example: APP_CLEAR
clear_txn = transaction.ApplicationClearStateTxn(user.address, sp, app_id)
# .. sign, send, wait
# example: APP_CLEAR
