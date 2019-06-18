import algod
import json
import unittest
import base64
import kmd
import transaction
import crypto
import encoding

# change these after starting the node and kmd

algodToken = ("81f40d7c4c781557dfd2a7361986e6653c4be5c8df9ccdc8b866058854d10528")
algodAddress = "http://localhost:8080"

kmdToken = "8c9ee2fc51bc74c5fd5e51dd29ecdadc2ce1cf32d41ee8db96881c0006955b8b"
kmdAddress = "http://localhost:7833"



# change this to False to test all or
# True to test none (then comment out annotation
# for the ones you want to test)
skipAll = False
reason = "with on/off switch"


class TestCrypto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(algodToken, algodAddress)
        cls.kcl = kmd.kmdClient(kmdToken, kmdAddress)
        cls.t = cls.kcl.initWalletHandle("0b214bb0d156ba8f95a032e8985a8f40", "wallet")["wallet_handle_token"]
    
    @unittest.skipIf(skipAll, reason)
    def test_signTransaction(self):
        # random addresses, does not actually matter what they are as long as ac1 is in the wallet
        ac1 = "2NHEELBACGPFEVBPRTI5AWLQHZ6JNP24YM26VC6YJ6B5LYT5XLKWVLAPVA"
        ac2 = "REUTCIMLMZKWSDNOHGNXR5IXJLM6V6GHEHIBR4744WHD5AI4GHXFVEL5XU"
        tr = transaction.PaymentTxn(ac1, 1000, 237170, 237180, 'testnet-v38.0', "4HkOQEL2o2bVh2P1wSpky3s6cwcEg/AAd5qlery942g=", ac2, 100)
        prk = self.kcl.exportKey(self.t, "wallet", ac1)["private_key"]
        stxstring, txid, sig = crypto.signTransaction(tr, prk)
        result = self.kcl.signTransaction(self.t, "wallet", tr)["signed_transaction"]
        self.assertEqual(stxstring, result)

    @unittest.skipIf(skipAll, reason)
    def test_multisig(self):
        ac1 = "2NHEELBACGPFEVBPRTI5AWLQHZ6JNP24YM26VC6YJ6B5LYT5XLKWVLAPVA"
        ac2 = "REUTCIMLMZKWSDNOHGNXR5IXJLM6V6GHEHIBR4744WHD5AI4GHXFVEL5XU"
        ac3 = "WALEWI3I7BRR23BGFRFX4QFOFDMBP6V6BYADZ4OFPMHINQU6VEUKF7U7VI"
        msig = transaction.Multisig(1, 2, [ac1, ac2])
        tr = transaction.PaymentTxn(msig.address(), 1000, 237170, 237180, 'testnet-v38.0', "4HkOQEL2o2bVh2P1wSpky3s6cwcEg/AAd5qlery942g=", ac3, 100, note=b"random note", closeRemainderTo=ac3)
        pk2 = self.kcl.exportKey(self.t, "wallet", ac2)["private_key"]
        msig1 = self.kcl.signMultisigTransaction(self.t, "wallet", tr, encoding.b32tob64(ac1), msig)["multisig"]
        msig3 = self.kcl.signMultisigTransaction(self.t, "wallet", tr, encoding.b32tob64(ac2), encoding.msgpack_decode(msig1))["multisig"]
        prestx = transaction.SignedTransaction(tr, multisig=encoding.msgpack_decode(msig1))
        preStxBytes = encoding.msgpack_encode(prestx)
        stx, txid = crypto.appendMultisigTransaction(pk2, encoding.msgpack_decode(msig1), preStxBytes)
        stx2 = transaction.SignedTransaction(tr, multisig=encoding.msgpack_decode(msig3))
        stx2 = encoding.msgpack_encode(stx2)
        self.assertEqual(stx, stx2)

    @unittest.skipIf(skipAll, reason)
    def test_generateAccount(self):
        sk, vk, a = crypto.generateAccount()
        self.assertTrue(encoding.isValidAddress(a))

if __name__ == "__main__":
    unittest.defaultTestLoader.sortTestMethodsUsing = None
    unittest.main(verbosity=2)
