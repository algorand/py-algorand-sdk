# py-algorand-sdk
[![Build Status](https://travis-ci.com/algorand/py-algorand-sdk.svg?token=T43Tcse3Cxcyi7xtqmyQ&branch=master)](https://travis-ci.com/algorand/py-algorand-sdk) [![PyPI version](https://badge.fury.io/py/py-algorand-sdk.svg)](https://badge.fury.io/py/py-algorand-sdk) [![Documentation Status](https://readthedocs.org/projects/py-algorand-sdk/badge/?version=latest&style=flat)](https://py-algorand-sdk.readthedocs.io/en/latest)

A python library for interacting with the Algorand network.

## Installation

Run ```$ pip3 install py-algorand-sdk``` to install the package.

Alternatively, choose a [distribution file](https://pypi.org/project/py-algorand-sdk/#files), and run ```$ pip3 install [file name]```.

## Quick start

Here's a simple example you can run without a node.

```python
from algosdk import account, encoding

# generate an account
private_key, address = account.generate_account()
print("Private key:", private_key)
print("Address:", address)

# check if the address is valid
if encoding.is_valid_address(address):
    print("The address is valid!")
else:
    print("The address is invalid.")
```

## Node setup

Follow the instructions in Algorand's [developer resources](https://developer.algorand.org/docs/introduction-installing-node) to install a node on your computer. 

## Running example.py

Before running [example.py](https://github.com/algorand/py-algorand-sdk/blob/master/example.py), start kmd:

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

Visit the [Algorand dispenser](https://bank.testnet.algorand.network/) and enter the account address to fund your account.

Next, in [params.py](https://github.com/algorand/py-algorand-sdk/blob/master/params.py), either update the tokens and addresses, or provide a path to the data directory.

You're now ready to run example.py!

## More examples

### using the Wallet class
Instead of always having to keep track of handles, IDs, and passwords for wallets, create a Wallet object to manage everything for you.
```python
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
```

### backing up a wallet with mnemonic

```python
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
You can also back up accounts using mnemonic.from_private_key().
### recovering a wallet using a backup phrase

```python
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
You can also recover accounts using mnemonic.to_private_key().

### writing transactions to file

If you don't want to send your transactions now, you can write them to file. This works with both signed and unsigned transactions.
```python
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
fee = params["fee"]

# create a transaction
amount = 10000
txn = transaction.PaymentTxn(sender, fee, last_round, last_round+100, gh, receiver, amount)

# write to file
txns = [txn]
transaction.write_to_file([txn], "pathtofile.tx")
```

We can also read transactions after writing them to file.

```python
# read from file
read_txns = transaction.retrieve_from_file("pathtofile.tx")
```

### manipulating multisig transactions

```python
import params
from algosdk import account, transaction, algod, encoding

acl = algod.AlgodClient(params.algod_token, params.algod_address)

# generate three accounts
private_key_1, account_1 = account.generate_account()
private_key_2, account_2 = account.generate_account()
private_key_3, account_3 = account.generate_account()

# create a multisig account
version = 1  # multisig version
threshold = 2  # how many signatures are necessary
msig = transaction.Multisig(version, threshold, [account_1, account_2])

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]
fee = params["fee"]

# create a transaction
sender = msig.address()
amount = 10000
txn = transaction.PaymentTxn(sender, fee, last_round, last_round+100, gh, account_3, amount)

# create a SignedTransaction object
mtx = transaction.MultisigTransaction(txn, msig)

# sign the transaction
mtx.sign(private_key_1)
mtx.sign(private_key_2)

# print encoded transaction
print(encoding.msgpack_encode(mtx))
```

### working with NoteField
We can put things in the "note" field of a transaction; here's an example with an auction bid. Note that you can put any bytes you want in the "note" field; you don't have to use the NoteField object.

```python
from algosdk import algod, mnemonic, transaction, account

passphrase = "teach chat health avocado broken avocado trick adapt parade witness damp gift behave harbor maze truth figure below scatter taste slow sustain aspect absorb nuclear"

acl = algod.AlgodClient("API-TOKEN", "API-Address")

# convert passphrase to secret key
sk = mnemonic.to_private_key(passphrase)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]
fee = params["fee"]

# Set other parameters
amount = 100000
note = "Some Text".encode()
receiver = "receiver Algorand Address"

# create the transaction
txn = transaction.PaymentTxn(account.address_from_private_key(sk), fee, last_round, last_round+1000, gh, receiver, amount, note=note)

# sign it
stx = txn.sign(sk)

# send it
txid = acl.send_transaction(stx)
```

We can also get the NoteField object back from its bytes:
```python
# decode notefield
decoded = encoding.msgpack_decode(base64.b64encode(note_field_bytes))
print(decoded.dictify())
```

### working with transaction group
```python
import params
from algosdk import algod, kmd, transaction

private_key_sender, sender = account.generate_account()
private_key_receiver, receiver = account.generate_account()

# create an algod and kmd client
acl = algod.AlgodClient(params.algod_token, params.algod_address)
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]
fee = params["fee"]

# create a transaction
amount = 10000
txn1 = transaction.PaymentTxn(sender, fee, last_round, last_round+100, gh, receiver, amount)
txn2 = transaction.PaymentTxn(receiver, fee, last_round, last_round+100, gh, sender, amount)

# get group id and assign it to transactions
gid = transaction.calculate_group_id([txn1, txn2])
txn1.transaction.group = gid
txn2.transaction.group = gid

# sign transactions
stxn1 = txn1.sign(private_key_sender)
stxn2 = txn2.sign(private_key_receiver)

# send them over network
acl.send_transactions([stxn1, stxn2])
```

### working with logic sig

Example below creates a LogicSig transaction signed by a program that never approves the transfer.

```python
import params
from algosdk import algod, transaction

program = b"\x01\x20\x01\x00\x22"  # int 0
lsig = transaction.LogicSig(program)
sender = lsig.address()

# create an algod client
acl = algod.AlgodClient(params.algod_token, params.algod_address)

# get suggested parameters
params = acl.suggested_params()
gen = params["genesisID"]
gh = params["genesishashb64"]
last_round = params["lastRound"]
fee = params["fee"]

# create a transaction
amount = 10000
txn = transaction.PaymentTxn(sender, fee, last_round, last_round+100, gh, receiver, amount)

# note, transaction is signed by logic only (no delegation)
# that means sender address must match to program hash
lstx = transaction.LogicSigTransaction(txn, lsig)
assert lstx.verify()

# send them over network
acl.send_transaction(lstx)
```

## Documentation
Documentation for the Python SDK is available at [py-algorand-sdk.readthedocs.io](https://py-algorand-sdk.readthedocs.io/en/latest/).

## License
py-algorand-sdk is licensed under a MIT license. See the [LICENSE](https://github.com/algorand/py-algorand-sdk/blob/master/LICENSE) file for details.
