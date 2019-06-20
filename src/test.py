import kmd
import json
import unittest
import transaction
import encoding
import algod
import base64
import crypto
import time
import mnemonic
import wordlist
import error

# change these after starting kmd
kmdToken = "bb24002c179d5d7b1ddf0735b9cfd2cb2ed922517fcd74b511ee0d65fa6c277b"
kmdAddress = "http://localhost:60187"

algodToken = "f40453efac65244a2763b195862aef0bea3abe21216b676d73936d2b4cc95518"
algodAddress = "http://localhost:8080"

# change these to match a wallet
wallet_name = "unencrypted-default-wallet"
wallet_pswd = ""

# account in the wallet that has a lot of algos
account_0 = "DAXGIQRDRA7IUAHSNLX2A5DSC3MTN3C7Z46N2PDMBOPRUGPJ2AITQDZFNI"

minTxnFee = 1000


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(algodToken, algodAddress)
        cls.kcl = kmd.kmdClient(kmdToken, kmdAddress)

    def test_handle(self):
        # create wallet; should raise error since wallet already exists
        self.assertRaises(error.KmdHTTPError, self.kcl.createWallet, wallet_name, wallet_pswd)

        # get the wallet ID
        wallets = self.kcl.listWallets()
        
        wallet_id = None
        for w in wallets:
            if w.name.__eq__(wallet_name):
                wallet_id = w.id
        
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
        txn = transaction.PaymentTxn(account_0, minTxnFee, last_round, last_round+100, gen, gh, account_1, 100000)

        # sign transaction with kmd
        signed_kmd = self.kcl.signTransaction(handle, wallet_pswd, txn)

        # get account_0 private key
        private_key_0 = self.kcl.exportKey(handle, wallet_pswd, account_0)

        # sign transaction with crypto
        signed_crypto, txid, sig = crypto.signTransaction(txn, private_key_0)

        # check that signing both ways results in the same thing
        self.assertEqual(encoding.msgpack_encode(signed_crypto), encoding.msgpack_encode(signed_kmd))

        # send the transaction
        send = self.acl.sendRawTransaction(signed_crypto)
        self.assertEqual(send, txid)

        """
        This part depends on how much traffic there is in the network;
        the time may vary but as long as traffic is not so heavy as to 
        max out blocks, this should work. This has been tested on a 
        private network (no traffic except for transactions produced here).
        """

        # wait for transaction to send
        time.sleep(3)

        # check for the transaction in pending transactions
        txn_info = self.acl.pendingTransactionInfo(txid)
        self.assertIn("type", txn_info)

        # wait for transaction to process
        time.sleep(6)

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
        txn = transaction.PaymentTxn(msig.address(), minTxnFee, last_round, last_round+100, gen, gh, account_0, 1000)
        
        # import multisig account
        msig_address = self.kcl.importMultisig(handle, msig)

        # export multisig account
        exported = self.kcl.exportMultisig(handle, msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create the preimage for the signed transaction
        preStx = transaction.SignedTransaction(txn, multisig=msig)
        
        # sign the multisig using kmd
        msig_1 = self.kcl.signMultisigTransaction(handle, wallet_pswd, account_1, preStx)
        signed_kmd = self.kcl.signMultisigTransaction(handle, wallet_pswd, account_2, msig_1)
        
        # sign the multisig using crypto
        stx1 = crypto.signMultisigTransaction(private_key_1, preStx)
        stx2 = crypto.signMultisigTransaction(private_key_2, preStx)
        signed_crypto, txid = crypto.mergeMultisigTransactions([stx1, stx2])
        
        # check that they are the same
        self.assertEqual(encoding.msgpack_encode(signed_crypto), encoding.msgpack_encode(signed_kmd))

        # delete accounts
        del_1 = self.kcl.deleteKey(handle, wallet_pswd, account_1)
        del_2 = self.kcl.deleteKey(handle, wallet_pswd, account_2)
        del_3 = self.kcl.deleteMultisig(handle, wallet_pswd, msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

    def test_getWalletInfo(self):
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


class TestUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(algodToken, algodAddress)
        cls.kcl = kmd.kmdClient(kmdToken, kmdAddress)

    def test_status(self):
        result = self.acl.status()["lastRound"]
        self.assertTrue(isinstance(result, int))

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
        zero_bytes = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        addr = encoding.encodeAddress(zero_bytes)
        expected_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon invest"
        result = mnemonic.fromKey(addr)
        self.assertEqual(expected_mnemonic, result)
        result = mnemonic.toKey(result)
        self.assertEqual(addr, result)

    def test_mnemonic(self):
        result = mnemonic.toKey(mnemonic.fromKey(account_0))
        self.assertEqual(result, account_0)
    
    def test_wordlist(self):
        result = mnemonic.checksum(bytes(wordlist.wordListRaw(), "ascii"))
        self.assertEqual(result, "venue")


if __name__ == "__main__":
    to_run = [TestUnit, TestIntegration]
    # to_run = [TestUnit]
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class) for test_class in to_run]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)

