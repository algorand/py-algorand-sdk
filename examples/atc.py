import base64
from algosdk import transaction, abi
from utils import get_accounts, get_algod_client, deploy_calculator_app

from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AccountTransactionSigner,
    TransactionWithSigner,
)


# example: ATC_CREATE
atc = AtomicTransactionComposer()
# example: ATC_CREATE

accts = get_accounts()
acct = accts.pop()

algod_client = get_algod_client()

# example: ATC_ADD_TRANSACTION
addr, sk = acct.address, acct.private_key

# Create signer object
signer = AccountTransactionSigner(sk)

# Get suggested params from the client
sp = algod_client.suggested_params()

# Create a transaction
ptxn = transaction.PaymentTxn(addr, sp, addr, 10000)

# Construct TransactionWithSigner
tws = TransactionWithSigner(ptxn, signer)

# Pass TransactionWithSigner to ATC
atc.add_transaction(tws)
# example: ATC_ADD_TRANSACTION


app_id = deploy_calculator_app(algod_client, acct)

# example: ATC_CONTRACT_INIT
with open("calculator/contract.json") as f:
    js = f.read()
contract = abi.Contract.from_json(js)
# example: ATC_CONTRACT_INIT

# example: ATC_ADD_METHOD_CALL

# Simple call to the `add` method, method_args can be any type but _must_
# match those in the method signature of the contract
atc.add_method_call(
    app_id,
    contract.get_method_by_name("add"),
    addr,
    sp,
    signer,
    method_args=[1, 1],
)
# example: ATC_ADD_METHOD_CALL


# example: ATC_RESULTS
# Other options:
# txngroup = atc.build_group()
# txids = atc.submit(client)
result = atc.execute(algod_client, 4)
for res in result.abi_results:
    print(res.return_value)
# example: ATC_RESULTS


my_method = abi.Method(
    name="box_ref_demo", args=[], returns=abi.Returns("void")
)
# example: ATC_BOX_REF
atc = AtomicTransactionComposer()
atc.add_method_call(
    app_id,
    my_method,
    addr,
    sp,
    signer,
    boxes=[[app_id, b"key"]],
)
# example: ATC_BOX_REF
