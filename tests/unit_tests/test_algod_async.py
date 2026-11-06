import base64
import unittest
from unittest.mock import MagicMock

from algosdk import account, encoding, error, transaction
from algosdk.v2client.algod import AlgodClient


class TestAlgodAsync(unittest.TestCase):
    def setUp(self):
        self.client = AlgodClient("fake_token", "http://localhost:4001")
        self.sk, self.addr = account.generate_account()
        sp = transaction.SuggestedParams(
            fee=1000,
            first=1,
            last=1000,
            gh="wGHE2Pwdvd7S12BL5Fa+pp3LENgQ04ITredAhPBI1cg=",
            gen="testnet-v1.0",
        )
        self.txn = transaction.PaymentTxn(self.addr, sp, self.addr, 1000)
        self.stx = self.txn.sign(self.sk)

    def test_send_raw_transaction_async_base64_str(self):
        self.client.algod_request = MagicMock(return_value={})
        raw_b64 = encoding.msgpack_encode(self.stx)
        expected_bytes = base64.b64decode(raw_b64)

        res = self.client.send_raw_transaction_async(raw_b64)

        self.assertEqual(res, {})
        self.client.algod_request.assert_called_once_with(
            "POST",
            "/transactions/async",
            data=expected_bytes,
            headers={"Content-Type": "application/x-binary"},
        )

    def test_send_raw_transaction_async_bytes(self):
        self.client.algod_request = MagicMock(return_value={})
        raw_b64_str = encoding.msgpack_encode(self.stx)
        raw_b64_bytes = raw_b64_str.encode("ascii")
        expected_bytes = base64.b64decode(raw_b64_bytes)

        res = self.client.send_raw_transaction_async(raw_b64_bytes)

        self.assertEqual(res, {})
        self.client.algod_request.assert_called_once_with(
            "POST",
            "/transactions/async",
            data=expected_bytes,
            headers={"Content-Type": "application/x-binary"},
        )

    def test_send_raw_transaction_async_custom_headers(self):
        self.client.algod_request = MagicMock(return_value={})
        raw_b64 = base64.b64encode(b"sample_txn_bytes").decode("ascii")

        res = self.client.send_raw_transaction_async(
            raw_b64, headers={"X-Custom-Header": "foo"}
        )

        self.assertEqual(res, {})
        self.client.algod_request.assert_called_once_with(
            "POST",
            "/transactions/async",
            data=b"sample_txn_bytes",
            headers={
                "X-Custom-Header": "foo",
                "Content-Type": "application/x-binary",
            },
        )

    def test_send_raw_transaction_async_rejects_non_json_format(self):
        with self.assertRaises(error.AlgodRequestError):
            self.client.send_raw_transaction_async(
                b"sample", response_format="msgpack"
            )

    def test_send_transaction_async(self):
        self.client.algod_request = MagicMock(return_value={})
        expected_bytes = base64.b64decode(encoding.msgpack_encode(self.stx))

        res = self.client.send_transaction_async(self.stx)

        self.assertEqual(res, {})
        self.client.algod_request.assert_called_once_with(
            "POST",
            "/transactions/async",
            data=expected_bytes,
            headers={"Content-Type": "application/x-binary"},
        )

    def test_send_transaction_async_unsigned_error(self):
        with self.assertRaises(AssertionError):
            self.client.send_transaction_async(self.txn)

    def test_send_transactions_async(self):
        self.client.algod_request = MagicMock(return_value={})
        stx_bytes = base64.b64decode(encoding.msgpack_encode(self.stx))
        expected_bytes = stx_bytes + stx_bytes

        res = self.client.send_transactions_async([self.stx, self.stx])

        self.assertEqual(res, {})
        self.client.algod_request.assert_called_once_with(
            "POST",
            "/transactions/async",
            data=expected_bytes,
            headers={"Content-Type": "application/x-binary"},
        )

    def test_send_transactions_async_unsigned_error(self):
        with self.assertRaises(AssertionError):
            self.client.send_transactions_async([self.stx, self.txn])


if __name__ == "__main__":
    unittest.main()
