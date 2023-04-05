from typing import Dict, Any
from algosdk import transaction
from utils import get_accounts, get_algod_client

algod_client = get_algod_client()


accts = get_accounts()
acct1 = accts.pop()
addr1, sk1 = acct1.address, acct1.private_key
acct2 = accts.pop()
addr2, sk2 = acct2.address, acct2.private_key

suggested_params = algod_client.suggested_params()

# example: ATOMIC_CREATE_TXNS
# payment from account 1 to account 2
txn_1 = transaction.PaymentTxn(addr1, suggested_params, addr2, 100000)
# payment from account 2 to account 1
txn_2 = transaction.PaymentTxn(addr2, suggested_params, addr1, 200000)
# example: ATOMIC_CREATE_TXNS


# example: ATOMIC_GROUP_TXNS
# Assign group id to the transactions (order matters!)
transaction.assign_group_id([txn_1, txn_2])
# Or, equivalently
# get group id and assign it to transactions
# gid = transaction.calculate_group_id([txn_1, txn_2])
# txn_1.group = gid
# txn_2.group = gid
# example: ATOMIC_GROUP_TXNS

# example: ATOMIC_GROUP_SIGN
# sign transactions
stxn_1 = txn_1.sign(sk1)
stxn_2 = txn_2.sign(sk2)
# example: ATOMIC_GROUP_SIGN

# example: ATOMIC_GROUP_ASSEMBLE
# combine the signed transactions into a single list
signed_group = [stxn_1, stxn_2]
# example: ATOMIC_GROUP_ASSEMBLE

# example: ATOMIC_GROUP_SEND

# Only the first transaction id is returned
tx_id = algod_client.send_transactions(signed_group)

# wait for confirmation
result: Dict[str, Any] = transaction.wait_for_confirmation(
    algod_client, tx_id, 4
)
print(f"txID: {tx_id} confirmed in round: {result.get('confirmed-round', 0)}")
# example: ATOMIC_GROUP_SEND
