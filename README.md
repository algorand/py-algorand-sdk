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
kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)

# create a wallet object
wallet = Wallet("wallet_name", "wallet_password", kcl)

# get wallet information
info = wallet.info()
print("Wallet name:", info.wallet.name)

# create an account
address = wallet.generateKey()
print("New account:", address)

# delete the account
delete = wallet.deleteKey(address)
print("Account deleted:", delete)
```

### backing up a wallet with mnemonic

```
import params
from algosdk import kmd, mnemonic
from algosdk.wallet import Wallet

# create a kmd client
kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)

# create a wallet object
wallet = Wallet("wallet_name", "wallet_password", kcl)

# get the wallet's master derivation key
mdk = wallet.exportMasterDerivationKey()
print("Master Derivation Key:", mdk)

# get the backup phrase
backup = mnemonic.fromMasterDerivationKey(mdk)
print("Wallet backup phrase:", backup)
```
You can also back up accounts using mnemonic.fromPrivateKey().
### recovering a wallet using a backup phrase

```
import params
from algosdk import kmd, mnemonic

# get the master derivation key from the mnemonic
backup = "such chapter crane ugly uncover fun kitten duty culture giant skirt reunion pizza pill web monster upon dolphin aunt close marble dune kangaroo ability merit"
mdk = mnemonic.toMasterDerivationKey(backup)

# create a kmd client
kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)

# recover the wallet by passing mdk when creating a wallet
kcl.createWallet("wallet_name", "wallet_password", master_deriv_key=mdk)
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
acl = algod.AlgodClient(params.algodToken, params.algodAddress)
kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)

# get suggested parameters
params = acl.suggestedParams()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]

# create a transaction
txn = transaction.PaymentTxn(sender, 1000, last_round, last_round+100, gh, receiver, 10000)

# write to file
txns = [txn]
transaction.writeToFile([txn], "pathtofile.tx")
```

We can also read transactions after writing them to file.

```
# read from file
read_txns = transaction.retrieveFromFile("pathtofile.tx")
```

### manipulating multisig transactions

```
import params
from algosdk import crypto, transaction, algod

acl = algod.AlgodClient(params.algodToken, params.algodAddress)

# generate three accounts
private_key_1, account_1 = crypto.generateAccount()
private_key_2, account_2 = crypto.generateAccount()
private_key_3, account_3 = crypto.generateAccount()

# create a multisig account
msig = transaction.Multisig(1, 2, [account_1, account_2])

# get suggested parameters
params = acl.suggestedParams()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]

# create a transaction
sender = msig.address()
txn = transaction.PaymentTxn(sender, 1000, last_round, last_round+100, gh, account_3, 10000)

# create a SignedTransaction object
stx = transaction.SignedTransaction(txn, multisig=msig)

# sign the transaction
signed_by_first = crypto.signMultisigTransaction(private_key_1, stx)
signed_by_both = crypto.signMultisigTransaction(private_key_2, signed_by_first)
```

