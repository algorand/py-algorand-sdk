# py-algorand-sdk

[![PyPI version](https://badge.fury.io/py/py-algorand-sdk.svg)](https://badge.fury.io/py/py-algorand-sdk)
[![Documentation Status](https://readthedocs.org/projects/py-algorand-sdk/badge/?version=latest&style=flat)](https://py-algorand-sdk.readthedocs.io/en/latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A python library for interacting with the Algorand network.

## Installation

Run `$ pip3 install py-algorand-sdk` to install the package.

Alternatively, choose a [distribution file](https://pypi.org/project/py-algorand-sdk/#files), and run `$ pip3 install [file name]`.

## Supported Python versions

py-algorand-sdk's minimum Python version policy attempts to balance several constraints.

* Make it easy for the community to use py-algorand-sdk by minimizing or excluding the need to customize Python installations.
* Provide maintainers with access to newer language features that produce more robust software.

Given these constraints, the minimum Python version policy is:
Target Python version on newest [Ubuntu LTS](https://wiki.ubuntu.com/Releases) released >= 6 months ago.

The rationale is:

* If a major Linux OS distribution bumps a Python version, then it's sufficiently available to the community for us to upgrade.
* The 6 month time buffer ensures we delay upgrades until the community starts using a recently released LTS version.

## SDK Development

Install dependencies

* `pip3 install -r requirements.txt`

Run tests

* `make docker-test`

Set up the Algorand Sandbox based test-harness without running the tests

* `make harness`

Format code

* `black .`

Update `algosdk/__init__.pyi` which allows downstream developers importing `algosdk` and using VSCode's PyLance to have improved type analysis

* `make generate-init`

Lint types

* `make mypy` (or `mypy algosdk`)

Check all lints required by the C.I. process

* `make lint`

Run non-test-harness related unit tests

* `make pytest-unit`

We use cucumber testing for all of our SDKs, including this one. Please refer to [algorand-sdk-testing](https://github.com/algorand/algorand-sdk-testing#readme) for guidance and existing tests that you may need to update. Depending on the type of update you wish to contribute, you may also need to have corresponding updates in the other SDKs (Go, JS, and Java). Feel welcome to ask for collaboration on that front. 

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
You can also set up a local [Algorand Sandbox](https://github.com/algorand/sandbox) with `make harness`.

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

Next, in [tokens.py](https://github.com/algorand/py-algorand-sdk/blob/master/examples/tokens.py), either update the tokens and addresses, or provide a path to the data directory. Alternatively, `tokens.py` also defaults to the sandbox harness configurations for algod and kmd, which can be brought up by running `make harness`.

You're now ready to run example.py!

## Documentation

Documentation for the Python SDK is available at [py-algorand-sdk.readthedocs.io](https://py-algorand-sdk.readthedocs.io/en/latest/).

## License

py-algorand-sdk is licensed under an MIT license. See the [LICENSE](https://github.com/algorand/py-algorand-sdk/blob/master/LICENSE) file for details.
