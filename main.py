from algosdk import algod
from algosdk import auction
from algosdk import constants
from algosdk import crypto
from algosdk import encoding
from algosdk import error
from algosdk import kmd
from algosdk import mnemonic
from algosdk import responses
from algosdk import transaction
from algosdk import wordlist
from algosdk import wallet
import params
import time

# to run tests:
import unittest
suite = unittest.TestLoader().discover("algosdk.tests")
result = unittest.TextTestRunner(verbosity=2).run(suite)

# acl = algod.AlgodClient(params.algodToken, params.algodAddress)
# kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)
