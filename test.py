import msgpack
import time
import base64
import json
import unittest
import params
import os
from algosdk import kmd
from algosdk import transaction
from algosdk import encoding
from algosdk import algod
from algosdk import crypto
from algosdk import mnemonic
from algosdk import wordlist
from algosdk import error
from algosdk import auction
from algosdk import constants
from algosdk import wallet


# change these to match a wallet
wallet_name = "unencrypted-default-wallet"
wallet_pswd = ""

# account in the wallet that has a lot of algos
account_0 = "DAXGIQRDRA7IUAHSNLX2A5DSC3MTN3C7Z46N2PDMBOPRUGPJ2AITQDZFNI"


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(params.algodToken, params.algodAddress)
        cls.kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)

    def test_auction(self):
        # get the default wallet
        wallets = self.kcl.listWallets()
        wallet_id = None
        for w in wallets:
            if w.name.__eq__(wallet_name):
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.initWalletHandle(wallet_id, wallet_pswd)

        # generate account with kmd
        account_1 = self.kcl.generateKey(handle, False)

        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # get account_0 private key
        private_key_0 = self.kcl.exportKey(handle, wallet_pswd, account_0)

        # create bid
        bid = auction.Bid(account_0, 10000, 260, "bid_id", account_1, "auc_id")
        sb = crypto.signBid(bid, private_key_0)
        nf = auction.NoteField(sb, constants.note_field_type_bid)

        # create transaction
        txn = transaction.PaymentTxn(account_0, constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_1, 100000, note=base64.b64decode(
                                         encoding.msgpack_encode(nf)), gen=gen)

        # sign transaction with crypto
        signed_crypto, txid, sig = crypto.signTransaction(txn, private_key_0)
        self.assertEqual(signed_crypto.getSignature(), sig)

        # send the transaction
        send = self.acl.sendRawTransaction(signed_crypto)
        self.assertEqual(send, crypto.getTxid(txn))

        # delete accounts
        del_1 = self.kcl.deleteKey(handle, wallet_pswd, account_1)
        self.assertTrue(del_1)

    def test_handle(self):
        # create wallet; should raise error since wallet already exists
        self.assertRaises(error.KmdHTTPError, self.kcl.createWallet,
                          wallet_name, wallet_pswd)

        # get the wallet ID
        wallets = self.kcl.listWallets()

        wallet_id = None
        for w in wallets:
            if w.name.__eq__(wallet_name):
                wallet_id = w.id

        # rename the wallet
        self.assertEqual(wallet_name + "newname", self.kcl.renameWallet(
                         wallet_id, wallet_pswd, wallet_name + "newname").name)

        # change it back
        self.assertEqual(wallet_name, self.kcl.renameWallet(wallet_id,
                         wallet_pswd, wallet_name).name)

        # get a new handle for the wallet
        handle = self.kcl.initWalletHandle(wallet_id, wallet_pswd)

        # get expiration time of handle
        time.sleep(1)
        exp_time = self.kcl.getWallet(handle).expires_seconds

        # renew the handle
        renewed_handle = self.kcl.renewWalletHandle(handle)
        new_exp_time = renewed_handle.expires_seconds
        self.assertGreaterEqual(new_exp_time, exp_time)

        # release the handle
        released = self.kcl.releaseWalletHandle(handle)
        self.assertTrue(released)

        # check that the handle has been released
        self.assertRaises(error.KmdHTTPError, self.kcl.getWallet, handle)

    def test_transaction(self):
        # get the default wallet
        wallets = self.kcl.listWallets()
        wallet_id = None
        for w in wallets:
            if w.name.__eq__(wallet_name):
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.initWalletHandle(wallet_id, wallet_pswd)

        # generate account with crypto and check if it's valid
        private_key_1, account_1 = crypto.generateAccount()
        self.assertTrue(encoding.isValidAddress(account_1))

        # import generated account
        import_key = self.kcl.importKey(handle, private_key_1)
        self.assertEqual(import_key, account_1)

        # generate account with kmd
        account_2 = self.kcl.generateKey(handle, False)

        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # create transaction
        txn = transaction.PaymentTxn(account_0, constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_1, 100000, gen=gen)

        # sign transaction with kmd
        signed_kmd = self.kcl.signTransaction(handle, wallet_pswd, txn)

        # get account_0 private key
        private_key_0 = self.kcl.exportKey(handle, wallet_pswd, account_0)

        # sign transaction with crypto
        signed_crypto, txid, sig = crypto.signTransaction(txn, private_key_0)

        # check that signing both ways results in the same thing
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # send the transaction
        send = self.acl.sendRawTransaction(signed_crypto)
        self.assertEqual(send, txid)

        # get transaction info in pending transactions
        self.assertEqual(self.acl.pendingTransactionInfo(txid)["tx"], txid)

        # wait for transaction to send
        self.acl.statusAfterBlock(last_round+2)

        # get transaction info three different ways
        info_1 = self.acl.transactionsByAddress(account_0, last_round)
        info_2 = self.acl.transactionInfo(account_0, txid)
        info_3 = self.acl.transactionByID(txid)
        self.assertIn("transactions", info_1)
        self.assertIn("type", info_2)
        self.assertIn("type", info_3)

        # delete accounts
        del_1 = self.kcl.deleteKey(handle, wallet_pswd, account_1)
        del_2 = self.kcl.deleteKey(handle, wallet_pswd, account_2)
        self.assertTrue(del_1)
        self.assertTrue(del_2)

    def test_multisig(self):
        # get the default wallet
        wallets = self.kcl.listWallets()
        wallet_id = None
        for w in wallets:
            if w.name.__eq__(wallet_name):
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.initWalletHandle(wallet_id, wallet_pswd)

        # generate two accounts with kmd
        account_1 = self.kcl.generateKey(handle, False)
        account_2 = self.kcl.generateKey(handle, False)

        # get their private keys
        private_key_1 = self.kcl.exportKey(handle, wallet_pswd, account_1)
        private_key_2 = self.kcl.exportKey(handle, wallet_pswd, account_2)

        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # create multisig account and transaction
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        txn = transaction.PaymentTxn(msig.address(), constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_0, 1000, gen=gen)

        # check that the multisig account is valid
        msig.validate()

        # import multisig account
        msig_address = self.kcl.importMultisig(handle, msig)

        # export multisig account
        exported = self.kcl.exportMultisig(handle, msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create the preimage for the signed transaction
        preStx = transaction.SignedTransaction(txn, multisig=msig)

        # sign the multisig using kmd
        msig_1 = self.kcl.signMultisigTransaction(handle, wallet_pswd,
                                                  account_1, preStx)
        signed_kmd = self.kcl.signMultisigTransaction(handle, wallet_pswd,
                                                      account_2, msig_1)

        # sign the multisig using crypto
        stx1 = crypto.signMultisigTransaction(private_key_1, preStx)
        stx2 = crypto.signMultisigTransaction(private_key_2, preStx)
        signed_crypto, txid = crypto.mergeMultisigTransactions([stx1, stx2])

        # check that they are the same
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # delete accounts
        del_1 = self.kcl.deleteKey(handle, wallet_pswd, account_1)
        del_2 = self.kcl.deleteKey(handle, wallet_pswd, account_2)
        del_3 = self.kcl.deleteMultisig(handle, wallet_pswd, msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

    def test_walletInfo(self):
        # get the default wallet
        wallets = self.kcl.listWallets()
        wallet_id = None
        for w in wallets:
            if w.name.__eq__(wallet_name):
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.initWalletHandle(wallet_id, wallet_pswd)

        # test listKeys
        listKeys = self.kcl.listKeys(handle)
        self.assertIn(account_0, listKeys)

        # test listMultisig
        listMultisig = self.kcl.listMultisig(handle)
        self.assertIsInstance(listMultisig, list)
        # either addresses are listed or there are no multisig accounts

        # test getting the master derivation key
        mdk = self.kcl.exportMasterDerivationKey(handle, wallet_pswd)
        self.assertIsInstance(mdk, str)

    def test_wallet(self):
        # initialize wallet
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)

        # get master derivation key
        mdk = w.exportMasterDerivationKey()

        # get mnemonic
        mn = w.getRecoveryPhrase()

        # make sure mnemonic can be converted back to mdk
        self.assertEqual(mdk, mnemonic.toMasterDerivationKey(mn))

        # generate account with crypto and check if it's valid
        private_key_1, account_1 = crypto.generateAccount()

        # import generated account
        import_key = w.importKey(private_key_1)
        self.assertEqual(import_key, account_1)

        # check that the account is in the wallet
        keys = w.listKeys()
        self.assertIn(account_1, keys)

        # generate account with kmd
        account_2 = w.generateKey()
        private_key_2 = w.exportKey(account_2)

        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # create transaction
        txn = transaction.PaymentTxn(account_0, constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_1, 100000, gen=gen)

        # sign transaction with wallet
        signed_kmd = w.signTransaction(txn)

        # get account_0 private key
        private_key_0 = w.exportKey(account_0)

        # sign transaction with crypto
        signed_crypto, txid, sig = crypto.signTransaction(txn, private_key_0)

        # check that signing both ways results in the same thing
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # create multisig account and transaction
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        txn = transaction.PaymentTxn(msig.address(), constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_0, 1000, gen=gen)

        # import multisig account
        msig_address = w.importMultisig(msig)

        # check that the multisig account is listed
        msigs = w.listMultisig()
        self.assertIn(msig_address, msigs)

        # export multisig account
        exported = w.exportMultisig(msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create the preimage for the signed transaction
        preStx = transaction.SignedTransaction(txn, multisig=msig)

        # sign the multisig using kmd
        msig_1 = w.signMultisigTransaction(account_1, preStx)
        signed_kmd = w.signMultisigTransaction(account_2, msig_1)

        # sign the multisig using crypto
        stx1 = crypto.signMultisigTransaction(private_key_1, preStx)
        signed_crypto = crypto.signMultisigTransaction(private_key_2, stx1)

        # check that they are the same
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # delete accounts
        del_1 = w.deleteKey(account_1)
        del_2 = w.deleteKey(account_2)
        del_3 = w.deleteMultisig(msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

        # test renaming the wallet
        w.rename(wallet_name + "1")
        self.assertEqual(wallet_name + "1", w.info().wallet.name)
        w.rename(wallet_name)
        self.assertEqual(wallet_name, w.info().wallet.name)

        # test releasing the handle
        w.releaseHandle()
        self.assertRaises(error.KmdHTTPError, self.kcl.getWallet, w.handle)

        # test handle automation
        w.info()

    def test_errors(self):
        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # get random private key
        random_private_key, account_1 = crypto.generateAccount()

        # create transaction
        txn = transaction.PaymentTxn(account_0, constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_0, 1000, gen=gen)

        # try to send transaction without signing
        self.assertRaises(error.AlgodHTTPError,
                          self.acl.sendRawTransaction, txn)

        # create multisig account with invalid version
        msig = transaction.Multisig(2, 2, [account_0, account_0])
        self.assertRaises(error.UnknownMsigVersionError, msig.validate)

        # change it to have invalid threshold
        msig.version = 1
        msig.threshold = 3
        self.assertRaises(error.InvalidThresholdError, msig.validate)

        # try to sign multisig transaction
        msig.threshold = 2
        self.assertRaises(error.BadTxnSenderError,
                          crypto.signMultisigTransaction, random_private_key,
                          transaction.SignedTransaction(txn, multisig=msig))

        # change sender address to be correct
        txn.sender = encoding.decodeAddress(msig.address())
        preStx = transaction.SignedTransaction(txn, multisig=msig)

        # try to sign with incorrect private key
        self.assertRaises(error.InvalidSecretKeyError,
                          crypto.signMultisigTransaction, random_private_key,
                          transaction.SignedTransaction(txn, multisig=msig))

        # get account private key
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)
        private_key_0 = w.exportKey(account_0)

        # create another multisig with different address
        msig_2 = transaction.Multisig(1, 2, [account_0, account_1])

        # try to merge with different addresses
        preStx_2 = transaction.SignedTransaction(txn, multisig=msig_2)
        self.assertRaises(error.MergeKeysMismatchError,
                          crypto.mergeMultisigTransactions, [preStx, preStx_2])

        # create another multisig with same address
        msig_3 = msig_2.getAccountFromSig()

        # add mismatched signatures
        msig_2.subsigs[0].signature = "sig2"
        msig_3.subsigs[0].signature = "sig3"

        # try to merge
        preStx_3 = transaction.SignedTransaction(txn, multisig=msig_3)
        self.assertRaises(error.DuplicateSigMismatchError,
                          crypto.mergeMultisigTransactions,
                          [preStx_2, preStx_3])

        # mnemonic with wrong checksum
        mn = ("abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon")
        self.assertRaises(error.WrongChecksumError, mnemonic.toKey, mn)

        # mnemonic of wrong length
        mn = "abandon abandon abandon"
        self.assertRaises(error.WrongMnemonicLengthError, mnemonic.toKey, mn)

        # key bytes of wrong length
        key = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertRaises(error.WrongKeyBytesLengthError,
                          mnemonic.fromKey, key)

        # key of wrong length
        address = "WRONG_LENGTH_TOO_SHORT"
        self.assertRaises(error.WrongKeyLengthError,
                          encoding.decodeAddress, address)

    def test_get(self):
        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # create keyreg transaction
        txn = transaction.KeyregTxn(account_0, constants.minTxnFee, last_round,
                                    last_round+100, gh, account_0,
                                    account_0, last_round, last_round+100, 100)
        # test get functions
        self.assertEqual(account_0, txn.getSelectionKey())
        self.assertEqual(account_0, txn.getVoteKey())

        # create transaction
        txn = transaction.PaymentTxn(account_0, constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_0, 100000, account_0)

        # get private key
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)
        private_key = w.exportKey(account_0)

        # sign transaction
        stx, txid, sig = crypto.signTransaction(txn, private_key)

        # test get functions
        self.assertEqual(account_0, txn.getSender())
        self.assertEqual(account_0, txn.getReceiver())
        self.assertEqual(gh, txn.getGenesisHash())
        self.assertEqual(account_0, txn.getCloseRemainderTo())
        self.assertEqual(stx.getSignature(), sig)

    def test_fileReadWrite(self):
        # get suggested parameters and fee
        params = self.acl.suggestedParams()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]

        # create transaction
        txn = transaction.PaymentTxn(account_0, constants.minTxnFee,
                                     last_round, last_round+100, gh,
                                     account_0, 1000)

        # get private key
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)
        private_key = w.exportKey(account_0)

        # sign transaction
        stx, txid, sig = crypto.signTransaction(txn, private_key)

        # write to file
        transaction.writeToFile([txn, stx], "raw.tx")

        # read from file
        txns = transaction.retrieveFromFile("raw.tx")

        # check that the transactions are still the same
        self.assertEqual(encoding.msgpack_encode(txn),
                         encoding.msgpack_encode(txns[0]))
        self.assertEqual(encoding.msgpack_encode(stx),
                         encoding.msgpack_encode(txns[1]))

        # delete the file
        os.remove("raw.tx")


class TestUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(params.algodToken, params.algodAddress)
        cls.kcl = kmd.kmdClient(params.kmdToken, params.kmdAddress)

    def test_health(self):
        result = self.acl.health()
        self.assertEqual(result, None)

    def test_statusAfterBlock(self):
        lastRound = self.acl.status()["lastRound"]
        currRound = self.acl.statusAfterBlock(lastRound-1)["lastRound"]
        self.assertEqual(lastRound, currRound)

    def test_pendingTransactions(self):
        result = self.acl.pendingTransactions(0)
        self.assertIn("truncatedTxns", result)

    def test_versions(self):
        result = self.acl.versions()
        self.assertIn("versions", result)

    def test_ledgerSupply(self):
        result = self.acl.ledgerSupply()
        self.assertIn("totalMoney", result)

    def test_blockInfo(self):
        lastRound = self.acl.status()["lastRound"]
        result = self.acl.blockInfo(lastRound)
        self.assertIn("hash", result)

    def test_getVersion(self):
        result = self.kcl.getVersion()
        self.assertIn("v1", result)

    def test_suggestedFee(self):
        result = self.acl.suggestedFee()
        self.assertIn("fee", result)

    def test_suggestedParams(self):
        result = self.acl.suggestedParams()
        self.assertIn("genesisID", result)

    def test_accountInfo(self):
        result = self.acl.accountInfo(account_0)
        self.assertEqual(result["address"], account_0)

    def test_zeroMnemonic(self):
        zero_bytes = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        expected_mnemonic = ("abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon invest")
        result = mnemonic.fromKey(zero_bytes)
        self.assertEqual(expected_mnemonic, result)
        result = mnemonic.toKey(result)
        self.assertEqual(zero_bytes, result)

    def test_mnemonic(self):
        result = mnemonic.toKey(mnemonic.fromKey(
                                encoding.decodeAddress(account_0)))
        self.assertEqual(result, encoding.decodeAddress(account_0))

    def test_mnemonicPrivateKey(self):
        priv_key, address = crypto.generateAccount()
        mn = mnemonic.fromPrivateKey(priv_key)
        self.assertEqual(len(mn.split(" ")), 25)
        self.assertEqual(priv_key, mnemonic.toPrivateKey(mn))

    def test_wordlist(self):
        result = mnemonic.checksum(bytes(wordlist.wordListRaw(), "ascii"))
        self.assertEqual(result, "venue")

    def test_msgpack(self):
        bid = ("gqFigqNiaWSGo2FpZAGjYXVjxCCokNFWl9DCqHrP9trjPICAMGOaRoX/OR+" +
               "M6tHWhfUBkKZiaWRkZXLEIP1rCXe2x5+exPBfU3CZwGPMY8mzwvglET+Qtg" +
               "fCPdCmo2N1cs8AAADN9kTOAKJpZM5JeDcCpXByaWNlzQMgo3NpZ8RAiR06J" +
               "4suAixy13BKHlw4VrORKzLT5CJr9n3YSj0Ao6byV23JHGU0yPf7u9/o4ECw" +
               "4Xy9hc9pWopLW97xKXRfA6F0oWI=")
        stxn = ("gqNzaWfEQGdpjnStb70k2iXzOlu+RSMgCYLe25wkUfbgRsXs7jx6rbW61i" +
                "vCs6/zGs3gZAZf4L2XAQak7OjMh3lw9MTCIQijdHhuiaNhbXTOAAGGoKNm" +
                "ZWXNA+iiZnbNcl+jZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk" +
                "8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1yw6NyY3bEIPRUuVDPVUFC7Jk3" +
                "+xDjHJfwWFDp+Wjy+Hx3cwL9ncVYo3NuZMQgGC5kQiOIPooA8mrvoHRyFt" +
                "k27F/PPN08bAufGhnp0BGkdHlwZaNwYXk=")
        paytxn = ("iaNhbXTOAAGGoKNmZWXNA+iiZnbNcq2jZ2Vuq25ldHdvcmstdjM4omdo" +
                  "xCBN/+nfiNPXLbuigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1zEaNy" +
                  "Y3bEIAZ2cvp4J0OiBy5eAHIX/njaRko955rEdN4AUNEl4rxTo3NuZMQg" +
                  "GC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGkdHlwZaNwYXk=")
        msigtxn = ("gqRtc2lng6ZzdWJzaWeSgqJwa8Qg1ke3gkLuR0MUN/Ku0oyiRVIm9P1" +
                   "QFDaiEhT5vtfLmd+hc8RAIEbfnhccjWfYQFQp/P4aJjATFdgaDDpnhy" +
                   "JF0tU/37CO5I5hhoCvUCRH/A/6X94Ewz9YEtk5dANEGKQW+/WyAIKic" +
                   "GvEIKgAZfZ4iDC+UY/P5F3tgs5rqeyYt08LT0c/D78u0V7KoXPEQCxU" +
                   "kQgTVC9lLpKVzcZGKesSCQcZL9UjXTzrteADicvcca7KT3WP0crGgAf" +
                   "J3a17Na5cykJzFEn7pq2SHgwD/QujdGhyAqF2AaN0eG6Jo2FtdM0D6K" +
                   "NmZWXNA+iiZnbNexSjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXL" +
                   "buigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds17eKNyY3bEIBguZEIj" +
                   "iD6KAPJq76B0chbZNuxfzzzdPGwLnxoZ6dARo3NuZMQgpuIJvJzW8E4" +
                   "uxsQGCW0S3n1u340PbHTB2zhtXo/AiI6kdHlwZaNwYXk=")
        keyregtxn = ("jKNmZWXNA+iiZnbNcoqjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfi" +
                     "NPXLbuigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1y7qZzZWxrZX" +
                     "nEIBguZEIjiD6KAPJq76B0chbZNuxfzzzdPGwLnxoZ6dARo3NuZMQ" +
                     "gGC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGkdHlwZaZr" +
                     "ZXlyZWendm90ZWZzdM1yiqZ2b3Rla2TNMDmndm90ZWtlecQgGC5kQ" +
                     "iOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGndm90ZWxzdM1y7g==")
        self.assertEqual(bid, encoding.msgpack_encode(
                         encoding.msgpack_decode(bid)))
        self.assertEqual(stxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(stxn)))
        self.assertEqual(paytxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(paytxn)))
        self.assertEqual(msigtxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(msigtxn)))
        self.assertEqual(keyregtxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(keyregtxn)))


if __name__ == "__main__":
    to_run = [TestUnit, TestIntegration]  # remove one to only one
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class)
              for test_class in to_run]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)
