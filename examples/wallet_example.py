# Example: using the Wallet class
# Instead of always having to keep track of handles, IDs, and passwords 
# for wallets, create a Wallet object to manage everything for you.

import params
from algosdk import kmd
from algosdk.wallet import Wallet

# create a kmd client
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# create a wallet object
wallet = Wallet("wallet_name", "wallet_password", kcl)

# get wallet information
info = wallet.info()
print("Wallet name:", info["wallet"]["name"])

# create an account
address = wallet.generate_key()
print("New account:", address)

# delete the account
delete = wallet.delete_key(address)
print("Account deleted:", delete)