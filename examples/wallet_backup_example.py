# Example: backing up a wallet with mnemonic

import tokens
from algosdk import kmd, mnemonic
from algosdk.wallet import Wallet

# create a kmd client
kcl = kmd.KMDClient(tokens.kmd_token, tokens.kmd_address)

# create a wallet object
wallet = Wallet("unencrypted-default-wallet", "", kcl)

# get the wallet's master derivation key
mdk = wallet.export_master_derivation_key()
print("Master Derivation Key:", mdk)

# get the backup phrase
backup = mnemonic.from_master_derivation_key(mdk)
print("Wallet backup phrase:", backup)
