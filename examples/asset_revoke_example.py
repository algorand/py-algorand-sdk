# Example: revoking assets

from algosdk import account, transaction

# this transaction must be sent by the asset's clawback manager
clawback_private_key, clawback_address = account.generate_account()

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
_, receiver = account.generate_account()  # where to send the revoked assets
_, target = account.generate_account()  # address to revoke assets from
amount = 100

index = 1234  # identifying index of the asset

# create the asset transfer transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetTransferTxn(
    clawback_address, sp, receiver, amount, index, revocation_target=target
)

# sign the transaction
signed_txn = txn.sign(clawback_private_key)
