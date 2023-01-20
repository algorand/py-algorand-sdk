# Example: updating asset configuration

from algosdk import account, transaction

# this transaction must be sent from the manager's account
manager_private_key, manager_address = account.generate_account()
# account that can freeze other accounts for this asset
_, new_freeze = account.generate_account()
# account able to update asset configuration
_, new_manager = account.generate_account()
# account allowed to take this asset from any other account
_, new_clawback = account.generate_account()
# account that holds reserves for this asset
_, new_reserve = account.generate_account()

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

index = 1234  # identifying index of the asset

# create the asset config transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetConfigTxn(
    manager_address,
    sp,
    manager=new_manager,
    reserve=new_reserve,
    freeze=new_freeze,
    clawback=new_clawback,
    index=index,
)

# sign the transaction
signed_txn = txn.sign(manager_private_key)
