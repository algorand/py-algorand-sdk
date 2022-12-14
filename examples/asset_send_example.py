# Example: sending assets

from algosdk import account, transaction

sender_private_key, sender_address = account.generate_account()

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
_, close_assets_to = account.generate_account()
_, receiver = account.generate_account()
amount = 100  # amount of assets to transfer

index = 1234  # identifying index of the asset

# create the asset transfer transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetTransferTxn(
    sender_address, sp, receiver, amount, index, close_assets_to
)

# sign the transaction
signed_txn = txn.sign(sender_private_key)
