# py-algorand-sdk

A python library for interacting with the Algorand network.

## Installation

Run ```$ pip3 install py-algorand-sdk``` to install the package.

Alternatively, visit https://pypi.org/project/py-algorand-sdk/#files, download a file, and run ```$ pip3 install [file name]``` to install the package.

## Node setup 

Follow the instructions at https://developer.algorand.org/docs/introduction-installing-node to install a node on your computer. 

## Running example.py

Before trying the examples, start kmd:

```
$ ./goal kmd start -d [data directory]
```

Next, create a wallet and an account:

```
$ ./goal wallet new [wallet name] -d [data directory]
```

```
$ ./goal account new -d [data directory] -w [wallet name]
```

Now visit https://bank.testnet.algorand.network/ and enter the account address to fund your account.

Next, in params.py, either update the tokens and addresses, or provide a path to the data directory.

You're now ready to run example.py!

## More examples

### using the Wallet class
Instead of always having to keep track of handles, IDs, and passwords for wallets, create a Wallet object to manage everything for you.
```
import params
from algosdk import kmd
from algosdk.wallet import Wallet

# create a kmd client
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# create a wallet object
wallet = Wallet("wallet_name", "wallet_password", kcl)

# get wallet information
info = wallet.info()
print("Wallet name:", info.wallet.name)

# create an account
address = wallet.generate_key()
print("New account:", address)

# delete the account
delete = wallet.delete_key(address)
print("Account deleted:", delete)
```

### backing up a wallet with mnemonic

```
import params
from algosdk import kmd, mnemonic
from algosdk.wallet import Wallet

# create a kmd client
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# create a wallet object
wallet = Wallet("wallet_name", "wallet_password", kcl)

# get the wallet's master derivation key
mdk = wallet.export_master_derivation_key()
print("Master Derivation Key:", mdk)

# get the backup phrase
backup = mnemonic.from_master_derivation_key(mdk)
print("Wallet backup phrase:", backup)
```
You can also back up accounts using mnemonic.fromPrivateKey().
### recovering a wallet using a backup phrase

```
import params
from algosdk import kmd, mnemonic

# get the master derivation key from the mnemonic
backup = "such chapter crane ugly uncover fun kitten duty culture giant skirt reunion pizza pill web monster upon dolphin aunt close marble dune kangaroo ability merit"
mdk = mnemonic.to_master_derivation_key(backup)

# create a kmd client
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# recover the wallet by passing mdk when creating a wallet
kcl.create_wallet("wallet_name", "wallet_password", master_deriv_key=mdk)
```
You can also recover accounts using mnemonic.toPrivateKey().
### writing transactions to file

If you don't want to send your transactions now, you can write them to file. This works with both signed and unsigned transactions.
```
import params
from algosdk import algod, kmd, transaction

sender = "sender_address"
receiver = "receiver_address"

# create an algod and kmd client
acl = algod.AlgodClient(params.algod_token, params.algod_address)
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]

# create a transaction
txn = transaction.PaymentTxn(sender, 1, last_round, last_round+100, gh, receiver, 10000)

# write to file
txns = [txn]
transaction.write_to_file([txn], "pathtofile.tx")
```

We can also read transactions after writing them to file.

```
# read from file
read_txns = transaction.retrieve_from_file("pathtofile.tx")
```

### manipulating multisig transactions

```
import params
from algosdk import crypto, transaction, algod

acl = algod.AlgodClient(params.algod_token, params.algod_address)

# generate three accounts
private_key_1, account_1 = crypto.generate_account()
private_key_2, account_2 = crypto.generate_account()
private_key_3, account_3 = crypto.generate_account()

# create a multisig account
msig = transaction.Multisig(1, 2, [account_1, account_2])

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]

# create a transaction
sender = msig.address()
txn = transaction.PaymentTxn(sender, 1000, last_round, last_round+100, gh, account_3, 10000)

# create a SignedTransaction object
stx = transaction.SignedTransaction(txn, multisig=msig)

# sign the transaction
signed_by_first = crypto.sign_multisig_transaction(private_key_1, stx)
signed_by_both = crypto.sign_multisig_transaction(private_key_2, signed_by_first)
```

