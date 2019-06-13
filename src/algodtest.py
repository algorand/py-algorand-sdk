from algod import AlgodClient
import json
import unittest

# change these after starting the node
algodToken = "81f40d7c4c781557dfd2a7361986e6653c4be5c8df9ccdc8b866058854d10528"
algodAddress = "http://localhost:8080"
reason = "with on/off switch"
# change this to False to test all or
# True to test none (then comment out annotation
# for the ones you want to test)
skipAll = True


class TestAlgod(unittest.TestCase):
    """Tests AlgodClient."""
    @classmethod
    def setUpClass(cls):
        cls.token = algodToken
        cls.address = algodAddress
        cls.client = AlgodClient(cls.token, cls.address)

    @unittest.skipIf(skipAll, reason)
    def test_status(self):
        result = self.client.status()["lastRound"]
        print(result)
        self.assertTrue(isinstance(result, int))

    @unittest.skipIf(skipAll, reason)
    def test_health(self):
        result = self.client.health()
        self.assertEqual(result, None)

    @unittest.skipIf(skipAll, reason)
    def test_statusAfterBlock(self):
        lastRound = self.client.status()["lastRound"]
        currRound = self.client.statusAfterBlock(lastRound-1)["lastRound"]
        self.assertEqual(lastRound, currRound)
        # newRound = self.client.statusAfterBlock(lastRound)["lastRound"]
        # self.assertEqual(lastRound + 1, newRound)

    @unittest.skipIf(skipAll, reason)
    def test_pendingTransactions(self):
        result = self.client.pendingTransactions(0)
        self.assertIn("truncatedTxns", result)
        print(result)

    @unittest.skipIf(skipAll, reason)
    def test_versions(self):
        result = self.client.versions()["versions"]
        self.assertIn("v1", result)

    @unittest.skipIf(skipAll, reason)
    def test_ledgerSupply(self):
        result = self.client.ledgerSupply()
        self.assertIn("round", result)
        self.assertIn("totalMoney", result)
        self.assertIn("onlineMoney", result)

    @unittest.skipIf(skipAll, reason)
    def test_accountInfo(self):
        addr = "2XQDFXOJ6OSTIF4ATCG6JRXKVBJ7IVZ6UBVDL53JP2MVQ3JCGUOPIPU3YU"
        result = self.client.accountInfo(addr)
        self.assertIn("status", result)
        self.assertEqual(result["address"], addr)
        print(result)

    # fromDate and toDate only work if indexer is enabled
    # should add extra test here for testing that
    # also should add round number safeguard if not archival node
    # also should consider adding other functions to cover these (see go sdk)
    @unittest.skipIf(skipAll, reason)
    def test_transactionsByAddress(self):
        lastRound = self.client.status()["lastRound"]
        addr = "2XQDFXOJ6OSTIF4ATCG6JRXKVBJ7IVZ6UBVDL53JP2MVQ3JCGUOPIPU3YU"
        result = self.client.transactionsByAddress(
            addr, lastRound-1, lastRound)
        print(result)
        self.assertEqual(result, {})

    @unittest.skipIf(skipAll, reason)
    def test_transactionInfo(self):
        addr = "EGM5CLMQUYJAQALAQ5J255UDRFHPUF75Q47QITYSDDTX76MHLO7HZYA32E"
        id = "BOSGMSQAXYWDFBMTHV7CUSD2CGZHST7JQA3YPEDQB4FYYU72GXVQ"  # nonexistent transaction
        result = self.client.transactionInfo(addr, id)
        self.assertIn("couldn't find the required transaction", result)

    @unittest.skipIf(skipAll, reason)
    def test_pendingTransactionInfo(self):
        result = self.client.pendingTransactions(1)
        result = result["truncatedTxns"]["transactions"]
        txn = result[0]
        id = txn["tx"]
        result = self.client.pendingTransactionInfo(id)
        self.assertEqual(result, txn)

    # only works if indexer is enabled
    @unittest.skipIf(skipAll, reason)
    def test_transactionByID(self):
        result = self.client.transactionByID(
            "M4HNA3GKCVHKT6O2T6GMT7MWFE2PRFDMXVGEA7I5VI3SPPGKUEIQ"
            )
        data = {
            "type": "pay",
            "tx": "M4HNA3GKCVHKT6O2T6GMT7MWFE2PRFDMXVGEA7I5VI3SPPGKUEIQ",
            "from": "2XQDFXOJ6OSTIF4ATCG6JRXKVBJ7IVZ6UBVDL53JP2MVQ3JCGUOPIPU3YU",
            "fee": 1991,
            "first-round": 140047,
            "last-round": 141047,
            "noteb64": "DzsIOf6SRtI=",
            "round": 140049,
            "payment": {
                "to": "OXC5VWAEDQSA67ERSBKHWMWVSIA5WFGFVZ7FY4FTERXJJOKQHHQ2T76FFE",
                "amount": 804
                },
            "genesisID": "testnet-v38.0",
            "genesishashb64": "4HkOQEL2o2bVh2P1wSpky3s6cwcEg/AAd5qlery942g="}
        self.assertEqual(result, data)

    @unittest.skipIf(skipAll, reason)
    def test_suggestedFee(self):
        result = self.client.suggestedFee()
        self.assertIn("fee", result)

    @unittest.skipIf(skipAll, reason)
    def test_suggestedParams(self):
        result = self.client.suggestedParams()
        print(result)
        self.assertIn("fee", result)
        self.assertIn("genesisID", result)
        self.assertIn("consensusVersion", result)

    @unittest.skipIf(skipAll, reason)
    def test_sendRawTransaction(self):
        print("NEED TO IMPLEMENT")

    @unittest.skipIf(skipAll, reason)
    def test_blockInfo(self):
        lastRound = self.client.status()["lastRound"]
        result = self.client.blockInfo(lastRound)
        self.assertIn("hash", result)


if __name__ == "__main__":
    unittest.defaultTestLoader.sortTestMethodsUsing = None
    unittest.main(verbosity=2)
