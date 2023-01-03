# Example: destroying an asset

from algosdk import account, transaction

# this transaction must be sent from the creator's account
creator_private_key, creator_address = account.generate_account()

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

index = 1234  # identifying index of the asset

# create the asset destroy transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetConfigTxn(
    creator_address, sp, index=index, strict_empty_address_check=False
)

# sign the transaction
signed_txn = txn.sign(creator_private_key)
