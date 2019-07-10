import time
import base64
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


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(params.algod_token, params.algod_address)
        cls.kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)
        w = wallet.Wallet(wallet_name, wallet_pswd, cls.kcl)
        keys = w.list_keys()
        max_balance = 0
        cls.account_0 = ""
        for k in keys:
            account_info = cls.acl.account_info(k)
            if account_info["amount"] > max_balance:
                max_balance = account_info["amount"]
                cls.account_0 = k

    def test_auction(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w.name == wallet_name:
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # generate account with kmd
        account_1 = self.kcl.generate_key(handle, False)

        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # get self.account_0 private key
        private_key_0 = self.kcl.export_key(handle, wallet_pswd,
                                            self.account_0)

        # create bid
        bid = auction.Bid(self.account_0, 10000, 260,
                          "bid_id", account_1, "auc_id")
        sb = bid.sign(private_key_0)
        nf = auction.NoteField(sb, constants.note_field_type_bid)

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, fee,
                                     last_round, last_round+100, gh,
                                     account_1, 100000, note=base64.b64decode(
                                        encoding.msgpack_encode(nf)), gen=gen)

        # sign transaction with crypto
        signed_crypto = txn.sign(private_key_0)

        # send transaction
        send = self.acl.send_raw_transaction(signed_crypto)
        self.assertEqual(send, txn.get_txid())
        del_1 = self.kcl.delete_key(handle, wallet_pswd, account_1)
        self.assertTrue(del_1)

    def test_handle(self):
        # create wallet; should raise error since wallet already exists
        self.assertRaises(error.KMDHTTPError, self.kcl.create_wallet,
                          wallet_name, wallet_pswd)

        # get the wallet ID
        wallets = self.kcl.list_wallets()

        wallet_id = None
        for w in wallets:
            if w.name == wallet_name:
                wallet_id = w.id

        # rename wallet
        self.assertEqual(wallet_name + "newname", self.kcl.rename_wallet(
                         wallet_id, wallet_pswd, wallet_name + "newname").name)

        # change it back
        self.assertEqual(wallet_name, self.kcl.rename_wallet(wallet_id,
                         wallet_pswd, wallet_name).name)

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # get expiration time of handle
        time.sleep(1)
        exp_time = self.kcl.get_wallet(handle).expires_seconds

        # renew the handle
        renewed_handle = self.kcl.renew_wallet_handle(handle)
        new_exp_time = renewed_handle.expires_seconds
        self.assertGreaterEqual(new_exp_time, exp_time)
        released = self.kcl.release_wallet_handle(handle)  # release the handle
        self.assertTrue(released)

        # check that the handle has been released
        self.assertRaises(error.KMDHTTPError, self.kcl.get_wallet, handle)

    def test_transaction(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w.name == wallet_name:
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # generate account and check if it's valid
        private_key_1, account_1 = crypto.generate_account()
        self.assertTrue(encoding.is_valid_address(account_1))

        # import generated account
        import_key = self.kcl.import_key(handle, private_key_1)
        self.assertEqual(import_key, account_1)

        # generate account with kmd
        account_2 = self.kcl.generate_key(handle, False)

        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, fee,
                                     last_round, last_round+100, gh,
                                     account_1, 100000, gen=gen)

        # sign transaction with kmd
        signed_kmd = self.kcl.sign_transaction(handle, wallet_pswd, txn)

        # get self.account_0 private key
        private_key_0 = self.kcl.export_key(handle, wallet_pswd,
                                            self.account_0)
        # sign transaction with crypto
        signed_crypto = txn.sign(private_key_0)
        txid = txn.get_txid()

        # check that signing both ways results in the same thing
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # send the transaction
        send = self.acl.send_raw_transaction(signed_crypto)
        self.assertEqual(send, txid)

        # get transaction info in pending transactions
        self.assertEqual(self.acl.pending_transaction_info(txid)["tx"], txid)

        # wait for transaction to send
        self.acl.status_after_block(last_round+2)

        # get transaction info three different ways
        info_1 = self.acl.transactions_by_address(self.account_0, last_round)
        info_2 = self.acl.transaction_info(self.account_0, txid)
        self.assertIn("transactions", info_1)
        self.assertIn("type", info_2)

        # delete accounts
        del_1 = self.kcl.delete_key(handle, wallet_pswd, account_1)
        del_2 = self.kcl.delete_key(handle, wallet_pswd, account_2)
        self.assertTrue(del_1)
        self.assertTrue(del_2)

    def test_multisig(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w.name == wallet_name:
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # generate two accounts with kmd
        account_1 = self.kcl.generate_key(handle, False)
        account_2 = self.kcl.generate_key(handle, False)

        # get their private keys
        private_key_1 = self.kcl.export_key(handle, wallet_pswd, account_1)
        private_key_2 = self.kcl.export_key(handle, wallet_pswd, account_2)

        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # create multisig account and transaction
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        txn = transaction.PaymentTxn(msig.address(), fee,
                                     last_round, last_round+100, gh,
                                     self.account_0, 1000, gen=gen)

        # check that the multisig account is valid
        msig.validate()

        # import multisig account
        msig_address = self.kcl.import_multisig(handle, msig)

        # export multisig account
        exported = self.kcl.export_multisig(handle, msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create multisig transaction
        mtx = transaction.MultisigTransaction(txn, msig)

        # sign using kmd
        msig_1 = self.kcl.sign_multisig_transaction(handle, wallet_pswd,
                                                    account_1, mtx)
        signed_kmd = self.kcl.sign_multisig_transaction(handle, wallet_pswd,
                                                        account_2, msig_1)

        # sign using crypto
        mtx1 = transaction.MultisigTransaction(txn, msig)
        mtx1.sign(private_key_1)
        mtx2 = transaction.MultisigTransaction(txn, msig)
        mtx2.sign(private_key_2)
        signed_crypto = transaction.MultisigTransaction.merge([mtx1, mtx2])

        # check that they are the same
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # delete accounts
        del_1 = self.kcl.delete_key(handle, wallet_pswd, account_1)
        del_2 = self.kcl.delete_key(handle, wallet_pswd, account_2)
        del_3 = self.kcl.delete_multisig(handle, wallet_pswd, msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

    def test_wallet_info(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w.name == wallet_name:
                wallet_id = w.id

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # test listKeys
        list_keys = self.kcl.list_keys(handle)
        self.assertIn(self.account_0, list_keys)

        # test listMultisig
        list_multisig = self.kcl.list_multisig(handle)
        self.assertIsInstance(list_multisig, list)
        # either addresses are listed or there are no multisig accounts

        # test getting the master derivation key
        mdk = self.kcl.export_master_derivation_key(handle, wallet_pswd)
        self.assertIsInstance(mdk, str)

    def test_wallet(self):
        # initialize wallet
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)

        # get master derivation key
        mdk = w.export_master_derivation_key()

        # get mnemonic
        mn = w.get_mnemonic()

        # make sure mnemonic can be converted back to mdk
        self.assertEqual(mdk, mnemonic.to_master_derivation_key(mn))

        # generate account with crypto and check if it's valid
        private_key_1, account_1 = crypto.generate_account()

        # import generated account
        import_key = w.import_key(private_key_1)
        self.assertEqual(import_key, account_1)

        # check that the account is in the wallet
        keys = w.list_keys()
        self.assertIn(account_1, keys)

        # generate account with kmd
        account_2 = w.generate_key()
        private_key_2 = w.export_key(account_2)

        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, fee,
                                     last_round, last_round+100, gh,
                                     account_1, 100000, gen=gen)

        # sign transaction with wallet
        signed_kmd = w.sign_transaction(txn)

        # get self.account_0 private key
        private_key_0 = w.export_key(self.account_0)

        # sign transaction with crypto
        signed_crypto = txn.sign(private_key_0)

        # check that signing both ways results in the same thing
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # create multisig account and transaction
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        txn = transaction.PaymentTxn(msig.address(), fee,
                                     last_round, last_round+100, gh,
                                     self.account_0, 1000, gen=gen)

        # import multisig account
        msig_address = w.import_multisig(msig)

        # check that the multisig account is listed
        msigs = w.list_multisig()
        self.assertIn(msig_address, msigs)

        # export multisig account
        exported = w.export_multisig(msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create multisig transaction
        mtx = transaction.MultisigTransaction(txn, msig)

        # sign the multisig using kmd
        msig_1 = w.sign_multisig_transaction(account_1, mtx)
        signed_kmd = w.sign_multisig_transaction(account_2, msig_1)

        # sign the multisig using crypto
        mtx1 = transaction.MultisigTransaction(txn, msig)
        mtx1.sign(private_key_1)
        mtx2 = transaction.MultisigTransaction(txn, msig)
        mtx2.sign(private_key_2)
        signed_crypto = transaction.MultisigTransaction.merge([mtx1, mtx2])

        # check that they are the same
        self.assertEqual(encoding.msgpack_encode(signed_crypto),
                         encoding.msgpack_encode(signed_kmd))

        # delete accounts
        del_1 = w.delete_key(account_1)
        del_2 = w.delete_key(account_2)
        del_3 = w.delete_multisig(msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

        # test renaming the wallet
        w.rename(wallet_name + "1")
        self.assertEqual(wallet_name + "1", w.info().wallet.name)
        w.rename(wallet_name)
        self.assertEqual(wallet_name, w.info().wallet.name)

        # test releasing the handle
        w.release_handle()
        self.assertRaises(error.KMDHTTPError, self.kcl.get_wallet, w.handle)

        # test handle automation
        w.info()

    def test_errors(self):
        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gen = params["genesisID"]
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # get random private key
        random_private_key, account_1 = crypto.generate_account()

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, fee,
                                     last_round, last_round+100, gh,
                                     self.account_0, 1000, gen=gen)

        # try to send transaction without signing
        self.assertRaises(error.AlgodHTTPError,
                          self.acl.send_raw_transaction, txn)

        # create multisig account with invalid version
        msig = transaction.Multisig(2, 2, [self.account_0, self.account_0])
        self.assertRaises(error.UnknownMsigVersionError, msig.validate)

        # change it to have invalid threshold
        msig.version = 1
        msig.threshold = 3
        self.assertRaises(error.InvalidThresholdError, msig.validate)

        # try to sign multisig transaction
        msig.threshold = 2
        mtx = transaction.MultisigTransaction(txn, msig)
        self.assertRaises(error.BadTxnSenderError,
                          mtx.sign, random_private_key)

        # change sender address to be correct
        txn.sender = encoding.decode_address(msig.address())
        mtx = transaction.MultisigTransaction(txn, msig)

        # try to sign with incorrect private key
        self.assertRaises(error.InvalidSecretKeyError,
                          mtx.sign, random_private_key)

        # create another multisig with different address
        msig_2 = transaction.Multisig(1, 2, [self.account_0, account_1])

        # try to merge with different addresses
        mtx_2 = transaction.MultisigTransaction(txn, msig_2)
        self.assertRaises(error.MergeKeysMismatchError,
                          transaction.MultisigTransaction.merge,
                          [mtx, mtx_2])

        # create another multisig with same address
        msig_3 = msig_2.get_account_from_sig()

        # add mismatched signatures
        msig_2.subsigs[0].signature = "sig2"
        msig_3.subsigs[0].signature = "sig3"

        # try to merge
        self.assertRaises(error.DuplicateSigMismatchError,
                          transaction.MultisigTransaction.merge,
                          [transaction.MultisigTransaction(txn, msig_2),
                           transaction.MultisigTransaction(txn, msig_3)])

        # mnemonic with wrong checksum
        mn = ("abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon")
        self.assertRaises(error.WrongChecksumError, mnemonic._to_key, mn)

        # mnemonic of wrong length
        mn = "abandon abandon abandon"
        self.assertRaises(error.WrongMnemonicLengthError, mnemonic._to_key, mn)

        # key bytes of wrong length
        key = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertRaises(error.WrongKeyBytesLengthError,
                          mnemonic._from_key, key)

        # key of wrong length
        address = "WRONG_LENGTH_TOO_SHORT"
        self.assertRaises(error.WrongKeyLengthError,
                          encoding.decode_address, address)

    def test_get(self):
        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # create keyreg transaction
        txn = transaction.KeyregTxn(self.account_0, fee,
                                    last_round, last_round+100, gh,
                                    self.account_0, self.account_0, last_round,
                                    last_round+100, 100)
        # test get functions
        self.assertEqual(self.account_0, txn.get_selection_key())
        self.assertEqual(self.account_0, txn.get_vote_key())

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, fee,
                                     last_round, last_round+100, gh,
                                     self.account_0, 100000, self.account_0)

        # get private key
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)
        private_key = w.export_key(self.account_0)

        # sign transaction
        stx = txn.sign(private_key)
        sig = stx.get_signature()

        # test get functions
        self.assertEqual(self.account_0, txn.get_sender())
        self.assertEqual(self.account_0, txn.get_receiver())
        self.assertEqual(gh, txn.get_genesis_hash())
        self.assertEqual(self.account_0, txn.get_close_remainder_to())
        self.assertEqual(stx.get_signature(), sig)

    def test_file_read_write(self):
        # get suggested parameters and fee
        params = self.acl.suggested_params()
        gh = params["genesishashb64"]
        last_round = params["lastRound"]
        fee = params["fee"]

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, fee,
                                     last_round, last_round+100, gh,
                                     self.account_0, 1000)

        # get private key
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)
        private_key = w.export_key(self.account_0)

        # sign transaction
        stx = txn.sign(private_key)

        # write to file
        transaction.write_to_file([txn, stx], "raw.tx")

        # read from file
        txns = transaction.retrieve_from_file("raw.tx")

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
        cls.acl = algod.AlgodClient(params.algod_token, params.algod_address)
        cls.kcl = kmd.KMDClient(params.kmd_token, params.kmd_address)
        w = wallet.Wallet(wallet_name, wallet_pswd, cls.kcl)
        keys = w.list_keys()
        max_balance = 0
        cls.account_0 = ""
        for k in keys:
            account_info = cls.acl.account_info(k)
            if account_info["amount"] > max_balance:
                max_balance = account_info["amount"]
                cls.account_0 = k

    def test_health(self):
        result = self.acl.health()
        self.assertEqual(result, None)

    def test_status_after_block(self):
        last_round = self.acl.status()["lastRound"]
        curr_round = self.acl.status_after_block(last_round)["lastRound"]
        self.assertEqual(last_round+1, curr_round)

    def test_pending_transactions(self):
        result = self.acl.pending_transactions(0)
        self.assertIn("truncatedTxns", result)

    def test_versions(self):
        result = self.acl.versions()
        self.assertIn("versions", result)

    def test_ledger_supply(self):
        result = self.acl.ledger_supply()
        self.assertIn("totalMoney", result)

    def test_block_info(self):
        last_round = self.acl.status()["lastRound"]
        result = self.acl.block_info(last_round)
        self.assertIn("hash", result)

    def test_get_version(self):
        result = self.kcl.get_version()
        self.assertIn("v1", result)

    def test_suggested_fee(self):
        result = self.acl.suggested_fee()
        self.assertIn("fee", result)

    def test_zero_mnemonic(self):
        zero_bytes = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        expected_mnemonic = ("abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon invest")
        result = mnemonic._from_key(zero_bytes)
        self.assertEqual(expected_mnemonic, result)
        result = mnemonic._to_key(result)
        self.assertEqual(zero_bytes, result)

    def test_mnemonic(self):
        result = mnemonic._to_key(mnemonic._from_key(
                                encoding.decode_address(self.account_0)))
        self.assertEqual(result, encoding.decode_address(self.account_0))

    def test_mnemonic_private_key(self):
        priv_key, address = crypto.generate_account()
        mn = mnemonic.from_private_key(priv_key)
        self.assertEqual(len(mn.split(" ")), constants.mnemonic_len)
        self.assertEqual(priv_key, mnemonic.to_private_key(mn))

    def test_address_from_private_key(self):
        priv_key, expected_address = crypto.generate_account()
        address = crypto.address_from_private_key(priv_key)
        self.assertEqual(address, expected_address)

    def test_wordlist(self):
        result = mnemonic._checksum(bytes(wordlist.word_list_raw(), "ascii"))
        self.assertEqual(result, "venue")

    def test_msgpack(self):
        self.maxDiff = None
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
