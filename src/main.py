import base64
import transaction
import encoding
import kmd
import crypto
import algod
from collections import OrderedDict

kmdToken = "8c9ee2fc51bc74c5fd5e51dd29ecdadc2ce1cf32d41ee8db96881c0006955b8b"
kmdAddress = "http://localhost:7833"
c = kmd.kmdClient(kmdToken, kmdAddress)

algodToken = ("81f40d7c4c781557dfd2a7361986e6653c4be5c8df9ccdc8b866058854d10528")
algodAddress = "http://localhost:8080"
a = algod.AlgodClient(algodToken, algodAddress)

ac1 = "Y54QNLK53ZSLFTRGVIANL7ILVRQAWYSEPSX7CXE7EE7BFGXD35O4PEG6WI"
ac2 = "H66LMSZVWGMKVOCTDTB7TKYC4DBSTUY6RTUOC5UTL7WHYQZCJP2AEONHFE"

tr = transaction.PaymentTxn(ac1, 1000, 237170, 237180, 'testnet-v38.0', "4HkOQEL2o2bVh2P1wSpky3s6cwcEg/AAd5qlery942g=", ac2, 100)

t = c.initWalletHandle("c1f3406894afc4f2b24ca83615a6e759",
                       "example-password")["wallet_handle_token"]

prk = c.exportKey(t, "example-password", ac1)["private_key"]

stxbytes, txid, sig = crypto.signTransaction(tr, prk)

print(a.sendRawTransaction(stxbytes))
