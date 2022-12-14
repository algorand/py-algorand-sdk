# Example: freezing or unfreezing an account

from algosdk import account, transaction

# this transaction must be sent from the account specified as the freeze manager for the asset
freeze_private_key, freeze_address = account.generate_account()

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
_, freeze_target = account.generate_account()

index = 1234  # identifying index of the asset

# create the asset freeze transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetFreezeTxn(
    freeze_address,
    sp,
    index=index,
    target=freeze_target,
    new_freeze_state=True,
)

# sign the transaction
signed_txn = txn.sign(freeze_private_key)
