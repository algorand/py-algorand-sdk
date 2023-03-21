import base64
from utils import get_algod_client, get_accounts
from algosdk import (
    transaction,
    encoding,
    atomic_transaction_composer,
    abi,
    dryrun_results,
)

algod_client = get_algod_client()
accts = get_accounts()

acct1 = accts.pop()
acct2 = accts.pop()

app_id = 123
my_method = abi.Method(
    name="cool_method", args=[], returns=abi.Returns("void")
)

# example: DEBUG_DRYRUN_DUMP
sp = algod_client.suggested_params()

atc = atomic_transaction_composer.AtomicTransactionComposer()
atc.add_method_call(app_id, my_method, acct1.address, sp, acct1.signer)
txns = atc.gather_signatures()

drr = transaction.create_dryrun(algod_client, txns)

# Write the file as binary result of msgpack encoding
with open("dryrun.msgp", "wb") as f:
    f.write(base64.b64decode(encoding.msgpack_encode(drr)))
# example: DEBUG_DRYRUN_DUMP

# example: DEBUG_DRYRUN_SUBMIT
# Create the dryrun request object
dryrun_request = transaction.create_dryrun(algod_client, txns)

# Pass dryrun request to algod server
dryrun_result = algod_client.dryrun(dryrun_request)
drr = dryrun_results.DryrunResponse(dryrun_result)

for txn in drr.txns:
    if txn.app_call_rejected():
        print(txn.app_trace())
# example: DEBUG_DRYRUN_SUBMIT
