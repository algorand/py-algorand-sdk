from kmd import kmdClient
import json
import unittest
import transaction
import encoding

# change these after starting kmd
kmdToken = "8c9ee2fc51bc74c5fd5e51dd29ecdadc2ce1cf32d41ee8db96881c0006955b8b"
kmdAddress = "http://localhost:7833"
skipAll = False
reason = "with on/off switch"

# before testing, make sure wallet is created
# and there are accounts in wallet
# put wallet information here to test
wallet_id = "0b214bb0d156ba8f95a032e8985a8f40"
wallet_pswd = "wallet"


class TestKMD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = kmdToken
        cls.address = kmdAddress
        cls.client = kmdClient(cls.token, cls.address)
        cls.handle = cls.client.initWalletHandle(wallet_id, wallet_pswd)["wallet_handle_token"]

    @unittest.skipIf(skipAll, reason)
    def test_getVersion(self):
        result = self.client.getVersion()
        self.assertIn("versions", result)

    @unittest.skipIf(skipAll, reason)
    def test_listWallets(self):
        result = self.client.listWallets()
        self.assertIn("wallets", result)

    @unittest.skipIf(skipAll, reason)
    def test_createWallet(self):
        result = self.client.createWallet("Wallet", wallet_pswd, "sqlite")
        self.assertEqual(result["message"], "wallet with same name already exists")

    @unittest.skipIf(skipAll, reason)
    def test_getWallet(self):
        result = self.client.getWallet(self.handle)
        self.assertEqual(result["wallet_handle"][wallet_pswd]["id"], wallet_id)


    @unittest.skipIf(skipAll, reason)
    def test_renewWalletHandle(self):
        handle = self.client.initWalletHandle(wallet_id, wallet_pswd)["wallet_handle_token"]
        exp = self.client.getWallet(handle)["wallet_handle"]["expires_seconds"]
        result = self.client.renewWalletHandle(handle)["wallet_handle"]["expires_seconds"]
        self.assertLessEqual(exp, result)

    @unittest.skipIf(skipAll, reason)
    def test_exportMasterDerivationKey(self):
        result = self.client.exportMasterDerivationKey(self.handle, wallet_pswd)
        self.assertIn("master_derivation_key", result)

    @unittest.skipIf(skipAll, reason)
    def test_listKeys(self):
        result = self.client.listKeys(self.handle)
        self.assertIn("addresses", result)

    @unittest.skipIf(skipAll, reason)
    def test_import_exportKey(self):
        address = self.client.listKeys(self.handle)["addresses"][0]
        exportresult = self.client.exportKey(self.handle, wallet_pswd, address)
        self.assertIn("private_key", exportresult)
        importresult = self.client.importKey(self.handle, exportresult["private_key"])
        self.assertEqual(importresult["message"], "key already exists in wallet")

    @unittest.skipIf(skipAll, reason)
    def test_generate_deleteKey(self):
        address = self.client.generateKey(self.handle, False)
        self.assertIn("address", address)
        address = address["address"]
        result = self.client.deleteKey(self.handle, wallet_pswd, address)
        self.assertEqual(result, {})

    @unittest.skipIf(skipAll, reason)
    def test_signTransaction(self):
        handle = self.client.initWalletHandle(wallet_id, wallet_pswd)["wallet_handle_token"]
        ac1 = self.client.generateKey(handle, True)["address"]
        ac2 = self.client.generateKey(handle, True)["address"]
        tr = transaction.PaymentTxn(ac1, 1000, 300, 400, 'testnet-v38.0', '4HkOQEL2o2bVh2P1wSpky3s6cwcEg/AAd5qlery942g=', ac2, 100)
        result = self.client.signTransaction(handle, wallet_pswd, tr)
        self.assertIn("signed_transaction", result)

    @unittest.skipIf(skipAll, reason)
    def test_listMultisig(self):
        result = self.client.listMultisig(self.handle)
        self.assertIn("addresses", result)

    @unittest.skipIf(skipAll, reason)
    def test_releaseWalletHandle(self):
        
        result = self.client.releaseWalletHandle(self.handle)
        self.assertEqual(result, {})

if __name__ == "__main__":
    unittest.defaultTestLoader.sortTestMethodsUsing = None
    unittest.main(verbosity=2)
