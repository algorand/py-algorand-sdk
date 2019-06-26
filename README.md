# py-algorand-sdk

A python library for interacting with the Algorand network.

## Installation

Run ```$ pip3 install algosdk``` to install the package.

Alternatively, download and unzip the package; then in the py-algorand-sdk directory, run ```$ python3 setup.py install```.

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
