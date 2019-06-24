from algosdk import algod
from algosdk import auction
from algosdk import crypto
from algosdk import encoding
from algosdk import error
from algosdk import kmd
from algosdk import mnemonic
from algosdk import responses
from algosdk import transaction
from algosdk import wordlist

# change these after starting the node and kmd
# algod info is in the algod.net and algod.token files in the node's data directory
# kmd info is in the kmd.net and kmd.token files in the kmd directory which is in data
# change these after starting the node and kmd
kmdToken = "ddf94bd098816efcd2e47e12b5fe20285f48257201ca1fe4067000a15f3fbd69"
kmdAddress = "http://localhost:59987"

algodToken = "d05db6ecec87954e747bd66668ec6dd3c3cef86d99ea88e8ca42a20f93f6be01"
algodAddress = "http://localhost:61186"


kcl = kmd.kmdClient(kmdToken, kmdAddress)
acl = algod.AlgodClient(algodToken, algodAddress)