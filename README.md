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






### writing transactions to file

If you don't want to send your transactions now, you can write them to file. This works with both signed and unsigned transactions.
```python
import params
from algosdk import algod, kmd
from algosdk.future import transaction

sender = "sender_address"
receiver = "receiver_address"

# create an algod and kmd client
acl = algod.AlgodClient(params.algod_token, params.algod_address)
kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)

# get suggested parameters
sp = acl.suggested_params()

# create a transaction
amount = 10000
txn = transaction.PaymentTxn(sender, sp, receiver, amount)

# write to file
txns = [txn]
transaction.write_to_file([txn], "pathtofile.tx")
```

We can also read transactions after writing them to file.

```python
# read from file
read_txns = transaction.retrieve_from_file("pathtofile.tx")
```


### working with logic sig

Example below creates a LogicSig transaction signed by a program that never approves the transfer.

```python
import params
from algosdk import algod
from algosdk.future import transaction

program = b"\x01\x20\x01\x00\x22"  # int 0
lsig = transaction.LogicSig(program)
sender = lsig.address()

# create an algod client
acl = algod.AlgodClient(params.algod_token, params.algod_address)

# get suggested parameters
sp = acl.suggested_params()

# create a transaction
amount = 10000
txn = transaction.PaymentTxn(sender, sp, receiver, amount)

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
from algosdk import account
from algosdk.future import transaction

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
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetConfigTxn(address, sp, total=total, manager=manager,
            reserve=reserve, freeze=freeze, clawback=clawback,
            unit_name=unitname, asset_name=assetname, url=url,
            metadata_hash=metadata, default_frozen=default_frozen)

# sign the transaction
signed_txn = txn.sign(private_key)
```
#### updating asset configuration
This transaction must be sent from the manager's account.
```python
from algosdk import account
from algosdk.future import transaction

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
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetConfigTxn(manager_address, sp, manager=new_manager, reserve=new_reserve,
            freeze=new_freeze, clawback=new_clawback, index=index)

# sign the transaction
signed_txn = txn.sign(manager_private_key)
```

#### destroying an asset
This transaction must be sent from the creator's account.
```python
from algosdk import account
from algosdk.future import transaction

creator_private_key = "creator private key"
creator_address = "creator address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

index = 1234 # identifying index of the asset

# create the asset destroy transaction
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetConfigTxn(creator_address, sp, index=index, strict_empty_address_check=False)

# sign the transaction
signed_txn = txn.sign(creator_private_key)
```

#### freezing or unfreezing an account
This transaction must be sent from the account specified as the freeze manager for the asset.
```python
from algosdk import account
from algosdk.future import transaction

freeze_private_key = "freeze private key"
freeze_address = "freeze address"

fee_per_byte = 10
first_valid_round = 1000
last_valid_round = 2000
genesis_hash = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
freeze_target = "address to be frozen or unfrozen"

index = 1234 # identifying index of the asset

# create the asset freeze transaction
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetFreezeTxn(freeze_address, sp, index=index, target=freeze_target,
            new_freeze_state=True)

# sign the transaction
signed_txn = txn.sign(freeze_private_key)
```

#### sending assets
```python
from algosdk import account
from algosdk.future import transaction

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
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetTransferTxn(sender_address, sp,
                receiver, amount, index, close_assets_to)

# sign the transaction
signed_txn = txn.sign(sender_private_key)
```

#### accepting assets
```python
from algosdk import account
from algosdk.future import transaction

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
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetTransferTxn(address, sp,
                receiver, amount, index)

# sign the transaction
signed_txn = txn.sign(private_key)
```

#### revoking assets
This transaction must be sent by the asset's clawback manager.
```python
from algosdk import account
from algosdk.future import transaction

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
sp = transaction.SuggestedParams(fee_per_byte, first_valid_round, last_valid_round, genesis_hash)
txn = transaction.AssetTransferTxn(clawback_address, sp,
                receiver, amount, index, revocation_target=target)

# sign the transaction
signed_txn = txn.sign(clawback_private_key)
```

## Documentation
Documentation for the Python SDK is available at [py-algorand-sdk.readthedocs.io](https://py-algorand-sdk.readthedocs.io/en/latest/).

## License
py-algorand-sdk is licensed under a MIT license. See the [LICENSE](https://github.com/algorand/py-algorand-sdk/blob/master/LICENSE) file for details.
