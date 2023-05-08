from typing import Dict, Any
from algosdk import transaction
from utils import get_accounts, get_algod_client

# Setup
algod_client = get_algod_client()
accounts = get_accounts()
acct1 = accounts.pop()
acct2 = accounts.pop()
acct3 = accounts.pop()


# example: ASSET_CREATE
# Account 1 creates an asset called `rug` with a total supply
# of 1000 units and sets itself to the freeze/clawback/manager/reserve roles
sp = algod_client.suggested_params()
txn = transaction.AssetConfigTxn(
    sender=acct1.address,
    sp=sp,
    default_frozen=False,
    unit_name="rug",
    asset_name="Really Useful Gift",
    manager=acct1.address,
    reserve=acct1.address,
    freeze=acct1.address,
    clawback=acct1.address,
    url="https://path/to/my/asset/details",
    total=1000,
    decimals=0,
)

# Sign with secret key of creator
stxn = txn.sign(acct1.private_key)
# Send the transaction to the network and retrieve the txid.
txid = algod_client.send_transaction(stxn)
print(f"Sent asset create transaction with txid: {txid}")
# Wait for the transaction to be confirmed
results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")

# grab the asset id for the asset we just created
created_asset = results["asset-index"]
print(f"Asset ID created: {created_asset}")
# example: ASSET_CREATE

# example: ASSET_CONFIG
sp = algod_client.suggested_params()
# Create a config transaction that wipes the
# reserve address for the asset
txn = transaction.AssetConfigTxn(
    sender=acct1.address,
    sp=sp,
    manager=acct1.address,
    reserve=None,
    freeze=acct1.address,
    clawback=acct1.address,
    strict_empty_address_check=False,
)
# Sign with secret key of manager
stxn = txn.sign(acct1.private_key)
# Send the transaction to the network and retrieve the txid.
txid = algod_client.send_transaction(stxn)
print(f"Sent asset config transaction with txid: {txid}")
# Wait for the transaction to be confirmed
results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")
# example: ASSET_CONFIG


# example: ASSET_INFO
# Retrieve the asset info of the newly created asset
asset_info = algod_client.asset_info(created_asset)
asset_params: Dict[str, Any] = asset_info["params"]
print(f"Asset Name: {asset_params['name']}")
print(f"Asset params: {list(asset_params.keys())}")
# example: ASSET_INFO


# example: ASSET_OPTIN
sp = algod_client.suggested_params()
# Create opt-in transaction
# asset transfer from me to me for asset id we want to opt-in to with amt==0
optin_txn = transaction.AssetOptInTxn(
    sender=acct2.address, sp=sp, index=created_asset
)
signed_optin_txn = optin_txn.sign(acct2.private_key)
txid = algod_client.send_transaction(signed_optin_txn)
print(f"Sent opt in transaction with txid: {txid}")

# Wait for the transaction to be confirmed
results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")
# example: ASSET_OPTIN

acct_info = algod_client.account_info(acct2.address)
matching_asset = [
    asset
    for asset in acct_info["assets"]
    if asset["asset-id"] == created_asset
].pop()
assert matching_asset["amount"] == 0
assert matching_asset["is-frozen"] is False


# example: ASSET_XFER
sp = algod_client.suggested_params()
# Create transfer transaction
xfer_txn = transaction.AssetTransferTxn(
    sender=acct1.address,
    sp=sp,
    receiver=acct2.address,
    amt=1,
    index=created_asset,
)
signed_xfer_txn = xfer_txn.sign(acct1.private_key)
txid = algod_client.send_transaction(signed_xfer_txn)
print(f"Sent transfer transaction with txid: {txid}")

results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")
# example: ASSET_XFER

acct_info = algod_client.account_info(acct2.address)
matching_asset = [
    asset
    for asset in acct_info["assets"]
    if asset["asset-id"] == created_asset
].pop()
assert matching_asset["amount"] == 1

# example: ASSET_FREEZE
sp = algod_client.suggested_params()
# Create freeze transaction to freeze the asset in acct2 balance
freeze_txn = transaction.AssetFreezeTxn(
    sender=acct1.address,
    sp=sp,
    index=created_asset,
    target=acct2.address,
    new_freeze_state=True,
)
signed_freeze_txn = freeze_txn.sign(acct1.private_key)
txid = algod_client.send_transaction(signed_freeze_txn)
print(f"Sent freeze transaction with txid: {txid}")

results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")
# example: ASSET_FREEZE

acct_info = algod_client.account_info(acct2.address)
matching_asset = [
    asset
    for asset in acct_info["assets"]
    if asset["asset-id"] == created_asset
].pop()
assert matching_asset["is-frozen"] is True

# example: ASSET_CLAWBACK
sp = algod_client.suggested_params()
# Create clawback transaction to freeze the asset in acct2 balance
clawback_txn = transaction.AssetTransferTxn(
    sender=acct1.address,
    sp=sp,
    receiver=acct1.address,
    amt=1,
    index=created_asset,
    revocation_target=acct2.address,
)
signed_clawback_txn = clawback_txn.sign(acct1.private_key)
txid = algod_client.send_transaction(signed_clawback_txn)
print(f"Sent clawback transaction with txid: {txid}")

results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")
# example: ASSET_CLAWBACK

acct_info = algod_client.account_info(acct2.address)
matching_asset = [
    asset
    for asset in acct_info["assets"]
    if asset["asset-id"] == created_asset
].pop()
assert matching_asset["amount"] == 0
assert matching_asset["is-frozen"] is True

# example: ASSET_OPT_OUT
sp = algod_client.suggested_params()
opt_out_txn = transaction.AssetTransferTxn(
    sender=acct2.address,
    sp=sp,
    index=created_asset,
    receiver=acct1.address,
    # an opt out transaction sets its close_asset_to parameter
    # it is always possible to close an asset to the creator
    close_assets_to=acct1.address,
    amt=0,
)
signed_opt_out = opt_out_txn.sign(acct2.private_key)
txid = algod_client.send_transaction(signed_opt_out)
print(f"Sent opt out transaction with txid: {txid}")

results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")
# example: ASSET_OPT_OUT


# example: ASSET_DELETE
sp = algod_client.suggested_params()
# Create asset destroy transaction to destroy the asset
destroy_txn = transaction.AssetDestroyTxn(
    sender=acct1.address,
    sp=sp,
    index=created_asset,
)
signed_destroy_txn = destroy_txn.sign(acct1.private_key)
txid = algod_client.send_transaction(signed_destroy_txn)
print(f"Sent destroy transaction with txid: {txid}")

results = transaction.wait_for_confirmation(algod_client, txid, 4)
print(f"Result confirmed in round: {results['confirmed-round']}")

# now, trying to fetch the asset info should result in an error
try:
    info = algod_client.asset_info(created_asset)
except Exception as e:
    print("Expected Error:", e)
# example: ASSET_DELETE
