# py-algorand-sdk

[![Build Status](https://travis-ci.com/algorand/py-algorand-sdk.svg?branch=master)](https://travis-ci.com/algorand/py-algorand-sdk)
[![PyPI version](https://badge.fury.io/py/py-algorand-sdk.svg)](https://badge.fury.io/py/py-algorand-sdk)
[![Documentation Status](https://readthedocs.org/projects/py-algorand-sdk/badge/?version=latest&style=flat)](https://py-algorand-sdk.readthedocs.io/en/latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A python library for interacting with the Algorand network.

## Installation

Run `$ pip3 install py-algorand-sdk` to install the package.

Alternatively, choose a [distribution file](https://pypi.org/project/py-algorand-sdk/#files), and run `$ pip3 install [file name]`.

## SDK Development

Install dependencies

- `pip install -r requirements.txt`

Run tests

- `make docker-test`

Format code:

- `black .`

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

Follow the instructions in Algorand's [developer resources](https://developer.algorand.org/docs/run-a-node/setup/install/) to install a node on your computer.

## Running examples/example.py

Before running [example.py](https://github.com/algorand/py-algorand-sdk/blob/master/examples/example.py), start kmd on a private network or testnet node:

```bash
./goal kmd start -d [data directory]
```

Next, create a wallet and an account:

```bash
./goal wallet new [wallet name] -d [data directory]
```

```bash
./goal account new -d [data directory] -w [wallet name]
```

Visit the [Algorand dispenser](https://bank.testnet.algorand.network/) and enter the account address to fund your account.

Next, in [tokens.py](https://github.com/algorand/py-algorand-sdk/blob/master/examples/tokens.py), either update the tokens and addresses, or provide a path to the data directory.

You're now ready to run example.py!

## Documentation

Documentation for the Python SDK is available at [py-algorand-sdk.readthedocs.io](https://py-algorand-sdk.readthedocs.io/en/latest/).

## License

py-algorand-sdk is licensed under an MIT license. See the [LICENSE](https://github.com/algorand/py-algorand-sdk/blob/master/LICENSE) file for details.
