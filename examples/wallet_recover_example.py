# Example: recovering a wallet using a backup phrase

import tokens
from algosdk import kmd, mnemonic

# get the master derivation key from the backup mnemonic
backup = "such chapter crane ugly uncover fun kitten duty culture giant skirt reunion pizza pill web monster upon dolphin aunt close marble dune kangaroo ability merit"
mdk = mnemonic.to_master_derivation_key(backup)

# create a kmd client
kcl = kmd.KMDClient(tokens.kmd_token, tokens.kmd_address)

# recover the wallet by passing mdk when creating a wallet
kcl.create_wallet("wallet_name", "wallet_password", master_deriv_key=mdk)

# list wallets; you should see the new wallet here
print(kcl.list_wallets())
