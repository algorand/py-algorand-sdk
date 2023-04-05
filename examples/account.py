from utils import get_accounts, get_algod_client
from algosdk import account, mnemonic
from algosdk import transaction

# example: ACCOUNT_GENERATE
private_key, address = account.generate_account()
print(f"address: {address}")
print(f"private key: {private_key}")
print(f"mnemonic: {mnemonic.from_private_key(private_key)}")
# example: ACCOUNT_GENERATE

# example: ACCOUNT_RECOVER_MNEMONIC
mn = "cost piano sample enough south bar diet garden nasty mystery mesh sadness convince bacon best patch surround protect drum actress entire vacuum begin abandon hair"
pk = mnemonic.to_private_key(mn)
print(f"Base64 encoded private key: {pk}")
addr = account.address_from_private_key(pk)
print(f"Address: {addr}")
# example: ACCOUNT_RECOVER_MNEMONIC

accts = get_accounts()
account_1 = accts.pop()
account_2 = accts.pop()
account_3 = accts.pop()

# example: MULTISIG_CREATE
version = 1  # multisig version
threshold = 2  # how many signatures are necessary
# create a Multisig given the set of participants and threshold
msig = transaction.Multisig(
    version,
    threshold,
    [account_1.address, account_2.address, account_3.address],
)
print("Multisig Address: ", msig.address())
# example: MULTISIG_CREATE

algod_client = get_algod_client()
sp = algod_client.suggested_params()
ptxn = transaction.PaymentTxn(
    account_1.address, sp, msig.address(), int(1e5)
).sign(account_1.private_key)
txid = algod_client.send_transaction(ptxn)
transaction.wait_for_confirmation(algod_client, txid, 4)
# dont check response, assume it worked

# example: MULTISIG_SIGN
msig_pay = transaction.PaymentTxn(
    msig.address(),
    sp,
    account_1.address,
    0,
    close_remainder_to=account_1.address,
)
msig_txn = transaction.MultisigTransaction(msig_pay, msig)
msig_txn.sign(account_2.private_key)
msig_txn.sign(account_3.private_key)
txid = algod_client.send_transaction(msig_txn)
result = transaction.wait_for_confirmation(algod_client, txid, 4)
print(
    f"Payment made from msig account confirmed in round {result['confirmed-round']}"
)
# example: MULTISIG_SIGN


# example: ACCOUNT_REKEY
# Any kind of transaction can contain a rekey
rekey_txn = transaction.PaymentTxn(
    account_1.address, sp, account_1.address, 0, rekey_to=account_2.address
)
signed_rekey = rekey_txn.sign(account_1.private_key)
txid = algod_client.send_transaction(signed_rekey)
result = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"rekey transaction confirmed in round {result['confirmed-round']}")

# Now we should get an error if we try to submit a transaction
# signed with account_1s private key
expect_err_txn = transaction.PaymentTxn(
    account_1.address, sp, account_1.address, 0
)
signed_expect_err_txn = expect_err_txn.sign(account_1.private_key)
try:
    txid = algod_client.send_transaction(signed_expect_err_txn)
except Exception as e:
    print("Expected error: ", e)

# But its fine if we sign it with the account we rekeyed to
signed_expect_err_txn = expect_err_txn.sign(account_2.private_key)
txid = algod_client.send_transaction(signed_expect_err_txn)
result = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"transaction confirmed in round {result['confirmed-round']}")

# rekey account1 back to itself so we can actually use it later
rekey_txn = transaction.PaymentTxn(
    account_1.address, sp, account_1.address, 0, rekey_to=account_1.address
)
signed_rekey = rekey_txn.sign(account_2.private_key)
txid = algod_client.send_transaction(signed_rekey)
result = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"rekey transaction confirmed in round {result['confirmed-round']}")
# example: ACCOUNT_REKEY
