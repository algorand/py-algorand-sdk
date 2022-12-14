# Example: accepting assets

from algosdk import account, transaction

private_key, address = account.generate_account()

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
receiver = address  # to start accepting assets, set receiver to sender
amount = 0  # to start accepting assets, set amount to 0

index = 1234  # identifying index of the asset

# create the asset accept transaction
sp = transaction.SuggestedParams(
    fee_per_byte, first_valid_round, last_valid_round, genesis_hash
)
txn = transaction.AssetTransferTxn(address, sp, receiver, amount, index)

# sign the transaction
signed_txn = txn.sign(private_key)
