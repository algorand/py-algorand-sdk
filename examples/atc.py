from algosdk.v2client import algod
from algosdk import transaction, abi
from utils import get_accounts

# example: ATC_CREATE
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    AccountTransactionSigner,
    TransactionWithSigner,
)

atc = AtomicTransactionComposer()
# example: ATC_CREATE

accts = get_accounts()
acct = accts.pop()

algod_address = "http://localhost:4001"
algod_token = "a" * 64
algod_client = algod.AlgodClient(algod_token, algod_address)

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

# example: ATC_CONTRACT_INIT
with open("path/to/contract.json") as f:
    js = f.read()
contract = abi.Contract.from_json(js)
# example: ATC_CONTRACT_INIT


# TODO: take it from contract object?
app_id = 123

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

# This method requires a `transaction` as its second argument.
# Construct the transaction and pass it in as an argument.
# The ATC will handle adding it to the group transaction and
# setting the reference in the application arguments.
ptxn = transaction.PaymentTxn(addr, sp, addr, 10000)
txn = TransactionWithSigner(ptxn, signer)
atc.add_method_call(
    app_id,
    contract.get_method_by_name("txntest"),
    addr,
    sp,
    signer,
    method_args=[10000, txn, 1000],
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


my_method = contract.get_method_by_name("add_member()void")
# example: ATC_BOX_REF
atc = AtomicTransactionComposer()
atc.add_method_call(
    app_id,
    my_method,
    addr,
    sp,
    signer,
    method_args=[1, 5],
    boxes=[[app_id, b"key"]],
)
# example: ATC_BOX_REF
