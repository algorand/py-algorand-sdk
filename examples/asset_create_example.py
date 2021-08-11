# Example: creating an asset

from algosdk import account
from algosdk.future import transaction

private_key, address = account.generate_account()  # creator
(
    _,
    freeze,
) = (
    account.generate_account()
)  # account that can freeze other accounts for this asset
(
    _,
    manager,
) = account.generate_account()  # account able to update asset configuration
(
    _,
    clawback,
) = (
    account.generate_account()
)  # account allowed to take this asset from any other account
(
    _,
    reserve,
) = account.generate_account()  # account that holds reserves for this asset

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

total = 100  # how many of this asset there will be
assetname = "assetname"
unitname = "unitname"
url = "website"
metadata = bytes(
    "fACPO4nRgO55j1ndAK3W6Sgc4APkcyFh", "ascii"
)  # should be a 32-byte hash
default_frozen = False  # whether accounts should be frozen by default

# create the asset creation transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetConfigTxn(
    address,
    sp,
    total=total,
    manager=manager,
    reserve=reserve,
    freeze=freeze,
    clawback=clawback,
    unit_name=unitname,
    asset_name=assetname,
    url=url,
    metadata_hash=metadata,
    default_frozen=default_frozen,
)

# sign the transaction
signed_txn = txn.sign(private_key)
