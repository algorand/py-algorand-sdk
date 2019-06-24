# py-algorand-sdk

A python library for interacting with the Algorand network.

## Installation

Download and unzip; then in the py-algorand-sdk directory, run 

```
$ python3 setup.py install
```

## Node setup 

Follow the instructions at https://developer.algorand.org/docs/introduction-installing-node to install a node on your computer. 

## Running example.py

Before trying the examples, start kmd:

```
$ ./goal kmd start -d [data directory]
```

Then find the following files: algod.net, algod.token, kmd.net, kmd.token. These contain the addresses and token you need to update at the top of example.py.

Next, create a wallet and an account:

```
$ ./goal wallet new [wallet name]
```

```
$ ./goal account new
```

Now visit https://bank.testnet.algorand.network/ and enter the account address to fund your account.

You're now ready to run example.py!
