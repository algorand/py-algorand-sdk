# Example: backing up an account with mnemonic

from algosdk import account, mnemonic

# generate an account
private_key, public_key = account.generate_account()
print("Public key:", public_key)
print("Private key:", private_key)

# get the backup phrase
backup = mnemonic.from_private_key(private_key)
print("Account backup phrase:", backup)

# recover the account from the backup phrase
recovered_private_key = mnemonic.to_private_key(backup)
recovered_public_key = mnemonic.to_public_key(backup)
print("Recovered public key:", recovered_public_key)
print("Recovered private key:", recovered_private_key)
