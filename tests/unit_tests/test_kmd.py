import base64
import unittest
from unittest.mock import MagicMock

from algosdk import encoding, kmd, transaction


class TestKMDClient(unittest.TestCase):
    def setUp(self):
        self.client = kmd.KMDClient(
            kmd_token="a" * 64, kmd_address="http://localhost:4002"
        )
        self.address = (
            "XDOV35UGGYEQHHN2UJSW4NQKS3IAFK2PYTGLK2CSUTDTXZ4EVRXTMEONEQ"
        )
        sp = transaction.SuggestedParams(
            fee=1000,
            first=1,
            last=1000,
            gh="SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
            flat_fee=True,
        )
        self.txn = transaction.PaymentTxn(
            sender=self.address,
            receiver=self.address,
            amt=1000,
            sp=sp,
        )
        # Create a mock signed transaction response
        stx = self.txn.sign(
            "r1bQx4F75q5uP4y1Zc/K9XhXk9p0f9Z/Z5wQ3U0v5hKq7/tZ7v5Z/Z5wQ3U0v5hKq7/tZ7v5Z/Z5wQ3U0v5hKg=="
        )
        self.mock_signed_tx_b64 = encoding.msgpack_encode(stx)

    def test_sign_transaction_without_signing_address(self):
        self.client.kmd_request = MagicMock(
            return_value={"signed_transaction": self.mock_signed_tx_b64}
        )

        res = self.client.sign_transaction(
            handle="test-handle", password="test-password", txn=self.txn
        )

        self.client.kmd_request.assert_called_once()
        call_args = self.client.kmd_request.call_args
        method, req = call_args[0]
        data = call_args[1]["data"]

        self.assertEqual(method, "POST")
        self.assertEqual(req, "/transaction/sign")
        self.assertEqual(data["wallet_handle_token"], "test-handle")
        self.assertEqual(data["wallet_password"], "test-password")
        self.assertNotIn("public_key", data)
        self.assertIsNotNone(res)

    def test_sign_transaction_with_signing_address(self):
        self.client.kmd_request = MagicMock(
            return_value={"signed_transaction": self.mock_signed_tx_b64}
        )

        res = self.client.sign_transaction(
            handle="test-handle",
            password="test-password",
            txn=self.txn,
            signing_address=self.address,
        )

        self.client.kmd_request.assert_called_once()
        call_args = self.client.kmd_request.call_args
        method, req = call_args[0]
        data = call_args[1]["data"]

        self.assertEqual(method, "POST")
        self.assertEqual(req, "/transaction/sign")
        self.assertIn("public_key", data)

        # Ensure public_key is valid base64-encoded 32-byte public key
        expected_pk_bytes = encoding.decode_address(self.address)
        actual_pk_bytes = base64.b64decode(data["public_key"])
        self.assertEqual(actual_pk_bytes, expected_pk_bytes)
        self.assertEqual(len(actual_pk_bytes), 32)
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()
