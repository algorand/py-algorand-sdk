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

### working with assets
Assets can be managed by sending three types of transactions: AssetConfigTxn, AssetFreezeTxn, and AssetTransferTxn. Shown below are examples of how to use these transactions.
#### creating an asset
```python
from algosdk import account, transaction

private_key, address = account.generate_account() # creator
_, freeze = account.generate_account() # account that can freeze other accounts for this asset
_, manager = account.generate_account() # account able to update asset configuration
_, clawback = account.generate_account() # account allowed to take this asset from any other account
_, reserve = account.generate_account() # account that holds reserves for this asset

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

total = 100 # how many of this asset there will be
assetname = "assetname"
unitname = "unitname"
url = "website"
metadata = bytes("fACPO4nRgO55j1ndAK3W6Sgc4APkcyFh", "ascii") # should be a 32-byte hash
default_frozen = False # whether accounts should be frozen by default

# create the asset creation transaction
txn = transaction.AssetConfigTxn(address, fee_per_byte, first_valid_round,
            last_valid_round, genesis_hash, total=total, manager=manager,
            reserve=reserve, freeze=freeze, clawback=clawback,
            unit_name=unitname, asset_name=assetname, url=url,
            metadata_hash=metadata, default_frozen=default_frozen)

# sign the transaction
signed_txn = txn.sign(private_key)
```
#### updating asset configuration
This transaction must be sent from the manager's account.
```python
from algosdk import account, transaction

manager_private_key = "manager private key"
manager_address = "manager address"
_, new_freeze = account.generate_account() # account that can freeze other accounts for this asset
_, new_manager = account.generate_account() # account able to update asset configuration
_, new_clawback = account.generate_account() # account allowed to take this asset from any other account
_, new_reserve = account.generate_account() # account that holds reserves for this asset

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

index = 1234 # identifying index of the asset

# create the asset config transaction
txn = transaction.AssetConfigTxn(manager_address, fee_per_byte, first_valid_round,
            last_valid_round, genesis_hash, manager=new_manager, reserve=new_reserve,
            freeze=new_freeze, clawback=new_clawback, index=index)

# sign the transaction
signed_txn = txn.sign(manager_private_key)
```

#### destroying an asset
This transaction must be sent from the creator's account.
```python
from algosdk import account, transaction

creator_private_key = "creator private key"
creator_address = "creator address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

index = 1234 # identifying index of the asset

# create the asset destroy transaction
txn = transaction.AssetConfigTxn(creator_address, fee_per_byte, first_valid_round, last_valid_round, genesis_hash,
                                         index=index, strict_empty_address_check=False)
# sign the transaction
signed_txn = txn.sign(creator_private_key)
```

#### freezing or unfreezing an account
This transaction must be sent from the account specified as the freeze manager for the asset.
```python
from algosdk import account, transaction

freeze_private_key = "freeze private key"
freeze_address = "freeze address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
freeze_target = "address to be frozen or unfrozen"

index = 1234 # identifying index of the asset

# create the asset freeze transaction
txn = transaction.AssetFreezeTxn(freeze_address, fee_per_byte, first_valid_round,
            last_valid_round, genesis_hash, index=index, target=freeze_target,
            new_freeze_state=True)

# sign the transaction
signed_txn = txn.sign(freeze_private_key)
```

#### sending assets
```python
from algosdk import account, transaction

sender_private_key = "freeze private key"
sender_address = "freeze address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
close_assets_to = "account to close assets to"
receiver = "account to receive assets"
amount = 100 # amount of assets to transfer

index = 1234 # identifying index of the asset

# create the asset transfer transaction
txn = transaction.AssetTransferTxn(sender_address, fee_per_byte, 
                first_valid_round, last_valid_round, genesis_hash,
                receiver, amount, index, close_assets_to)

# sign the transaction
signed_txn = txn.sign(sender_private_key)
```

#### accepting assets
```python
from algosdk import account, transaction

private_key = "freeze private key"
address = "freeze address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
receiver = address # to start accepting assets, set receiver to sender
amount = 0 # to start accepting assets, set amount to 0

index = 1234 # identifying index of the asset

# create the asset accept transaction
txn = transaction.AssetTransferTxn(address, fee_per_byte, 
                first_valid_round, last_valid_round, genesis_hash,
                receiver, amount, index)

# sign the transaction
signed_txn = txn.sign(private_key)
```

#### revoking assets
This transaction must be sent by the asset's clawback manager.
```python
from algosdk import account, transaction

clawback_private_key = "clawback private key"
clawback_address = "clawback address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
receiver = "receiver address" # where to send the revoked assets
target = "revocation target" # address to revoke assets from
amount = 100

index = 1234 # identifying index of the asset

# create the asset transfer transaction
txn = transaction.AssetTransferTxn(clawback_address, fee_per_byte, 
                first_valid_round, last_valid_round, genesis_hash,
                receiver, amount, index, revocation_target=target)

# sign the transaction
signed_txn = txn.sign(clawback_private_key)
```

## Documentation
Documentation for the Python SDK is available at [py-algorand-sdk.readthedocs.io](https://py-algorand-sdk.readthedocs.io/en/latest/).

## License
py-algorand-sdk is licensed under a MIT license. See the [LICENSE](https://github.com/algorand/py-algorand-sdk/blob/master/LICENSE) file for details.
