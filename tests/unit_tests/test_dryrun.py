import unittest
from unittest.mock import Mock

from algosdk.future import transaction
from algosdk.testing import dryrun


class TestDryrun(dryrun.DryrunTestCaseMixin, unittest.TestCase):
    def setUp(self):
        self.mock_response = dict(error=None, txns=[])

        self.algo_client = Mock()
        self.algo_client.dryrun = Mock()

        def response(dr):
            return self.mock_response

        self.algo_client.dryrun.side_effect = response

    def test_create_request(self):
        helper = dryrun.Helper
        with self.assertRaises(TypeError):
            helper.build_dryrun_request(10)

        drr = helper.build_dryrun_request("int 1")
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "lsig")
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)

        drr = helper.build_dryrun_request(
            "int 1", lsig=dict(args=[b"123", b"456"])
        )
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "lsig")
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)
        self.assertEqual(drr.txns[0].lsig.args, [b"123", b"456"])

        drr = helper.build_dryrun_request(b"\x02")
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)
        self.assertEqual(drr.txns[0].lsig.logic, b"\x02")

        drr = helper.build_dryrun_request(
            b"\x02", lsig=dict(args=[b"123", b"456"])
        )
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)
        self.assertEqual(drr.txns[0].lsig.logic, b"\x02")
        self.assertEqual(drr.txns[0].lsig.args, [b"123", b"456"])

        with self.assertRaises(TypeError):
            drr = helper.build_dryrun_request(b"\x02", lsig=dict(testkey=1))

        drr = helper.build_dryrun_request("int 1", app=dict())
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertNotEqual(drr.sources[0].app_index, 0)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )
        self.assertEqual(drr.txns[0].transaction.index, 0)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=None))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertNotEqual(drr.sources[0].app_index, 0)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )
        self.assertEqual(drr.txns[0].transaction.index, 0)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=0))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertNotEqual(drr.sources[0].app_index, 0)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )
        self.assertEqual(drr.txns[0].transaction.index, 0)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=1))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertEqual(drr.sources[0].app_index, 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )
        self.assertEqual(drr.txns[0].transaction.index, 1)

        drr = helper.build_dryrun_request(
            "int 1", app=dict(app_idx=1, on_complete=0)
        )
        self.assertEqual(drr.sources[0].field_name, "approv")

        drr = helper.build_dryrun_request(
            "int 1", app=dict(on_complete=transaction.OnComplete.ClearStateOC)
        )
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "clearp")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )

        drr = helper.build_dryrun_request(b"\x02", app=dict())
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].params.approval_program, b"\x02")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )

        drr = helper.build_dryrun_request(b"\x02", app=dict(on_complete=0))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].params.approval_program, b"\x02")
        self.assertIsNone(drr.apps[0].params.clear_state_program)
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )

        drr = helper.build_dryrun_request(
            b"\x02", app=dict(on_complete=transaction.OnComplete.ClearStateOC)
        )
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertEqual(len(drr.apps), 1)
        self.assertIsNone(drr.apps[0].params.approval_program)
        self.assertEqual(drr.apps[0].params.clear_state_program, b"\x02")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(
            drr.txns[0].transaction, transaction.ApplicationCallTxn
        )

        with self.assertRaises(TypeError):
            drr = helper.build_dryrun_request(b"\x02", app=dict(testkey=1))

    def test_pass_reject(self):
        self.mock_response = dict(
            error=None, txns=[{"logic-sig-messages": ["PASS"]}]
        )
        self.assertPass("int 1")
        with self.assertRaises(AssertionError):
            self.assertReject("int 1")

        self.mock_response = dict(
            error=None, txns=[{"app-call-messages": ["PASS"]}]
        )
        self.assertPass("int 1", app=dict(on_complete=0))
        with self.assertRaises(AssertionError):
            self.assertReject("int 1")

        self.assertPass(self.mock_response)
        with self.assertRaises(AssertionError):
            self.assertReject(self.mock_response)

        self.mock_response = dict(
            error=None, txns=[{"logic-sig-messages": ["REJECT"]}]
        )
        self.assertReject("int 1")
        with self.assertRaises(AssertionError):
            self.assertPass("int 1")

        self.assertReject(self.mock_response)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response)

        self.mock_response = dict(
            error=None, txns=[{"app-call-messages": ["PASS"]}]
        )
        self.assertPass(self.mock_response, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertReject(self.mock_response, txn_index=0)

        with self.assertRaisesRegex(AssertionError, r"out of range \[0, 1\)"):
            self.assertPass(self.mock_response, txn_index=1)

        with self.assertRaisesRegex(AssertionError, r"out of range \[0, 1\)"):
            self.assertReject(self.mock_response, txn_index=1)

        self.mock_response = dict(
            error=None,
            txns=[
                {"app-call-messages": ["PASS"]},
                {"app-call-messages": ["PASS"]},
            ],
        )
        self.assertPass(self.mock_response, txn_index=0)
        self.assertPass(self.mock_response, txn_index=1)
        self.assertPass(self.mock_response)

        self.mock_response = dict(
            error=None,
            txns=[
                {"app-call-messages": ["PASS"]},
                {"app-call-messages": ["REJECT"]},
            ],
        )
        self.assertPass(self.mock_response, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response, txn_index=1)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response)

        with self.assertRaises(AssertionError):
            self.assertReject(self.mock_response, txn_index=0)
        self.assertReject(self.mock_response, txn_index=1)
        self.assertReject(self.mock_response)

        self.mock_response = dict(
            error=None,
            txns=[
                {"app-call-messages": ["REJECT"]},
                {"app-call-messages": ["REJECT"]},
            ],
        )
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response, txn_index=1)

        self.assertReject(self.mock_response)
        self.assertReject(self.mock_response, txn_index=0)
        self.assertReject(self.mock_response, txn_index=1)

    def test_no_error(self):
        self.mock_response = dict(error=None, txns=None)
        self.assertNoError("int 1")

        self.mock_response = dict(error="", txns=None)
        self.assertNoError("int 1")

        self.mock_response = dict(
            error="Dryrun Source[0]: :3 + arg 0 wanted type uint64", txns=None
        )
        with self.assertRaises(AssertionError):
            self.assertNoError("byte 0x10\nint 1\n+")

        self.mock_response = dict(
            error="", txns=[{"logic-sig-trace": [{"line": 1}]}]
        )
        self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertError("int 1")

        self.mock_response = dict(
            error="", txns=[{"app-call-trace": [{"line": 1}]}]
        )
        self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertError("int 1")

        self.mock_response = dict(
            error="",
            txns=[
                {
                    "logic-sig-trace": [
                        {"line": 1},
                        {"error": "test", "line": 2},
                    ]
                }
            ],
        )
        self.assertError("int 1", "logic 0 failed")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")

        self.mock_response = dict(
            error="",
            txns=[
                {"app-call-trace": [{"line": 1}, {"error": "test", "line": 2}]}
            ],
        )

        self.assertError("int 1", "app 0 failed")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")

        self.assertError("int 1", txn_index=0)

        self.mock_response = dict(
            error="",
            txns=[
                {
                    "app-call-trace": [
                        {"line": 1},
                        {"error": "test1", "line": 2},
                    ]
                },
                {
                    "logic-sig-trace": [
                        {"line": 1},
                        {"error": "test2", "line": 2},
                    ]
                },
            ],
        )
        self.assertError("int 1", txn_index=0)
        self.assertError("int 1", txn_index=1)
        self.assertError("int 1")

        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1", txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1", txn_index=1)

        self.mock_response = dict(
            error="",
            txns=[
                {"app-call-trace": [{"line": 1}, {"line": 2}]},
                {
                    "logic-sig-trace": [
                        {"line": 1},
                        {"error": "test2", "line": 2},
                    ]
                },
            ],
        )
        self.assertNoError("int 1", txn_index=0)
        self.assertError("int 1", txn_index=1)
        self.assertError("int 1")

        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1", txn_index=1)

    def test_global_state(self):
        txn_res1 = {
            "global-delta": [
                dict(
                    key="test",
                    value=dict(action=1, uint=2),
                )
            ],
        }
        txn_res2 = {
            "global-delta": [
                dict(
                    key="key",
                    value=dict(action=1, uint=2),
                )
            ],
        }
        self.mock_response = dict(error=None, txns=[txn_res1])
        value = dict(key="test", value=dict(action=1, uint=2))
        self.assertGlobalStateContains("int 1", value, app=dict(on_complete=0))
        self.assertGlobalStateContains(
            self.mock_response, value, app=dict(on_complete=0)
        )

        self.mock_response = dict(
            error=None,
            txns=[
                {
                    "global-delta": [
                        dict(
                            key="test",
                            value=dict(action=2, bytes="test"),
                        )
                    ],
                }
            ],
        )
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains("int 1", value)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value)

        self.mock_response = dict(error=None, txns=[txn_res2])
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains("int 1", value)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value)

        self.mock_response = dict(error=None, txns=[txn_res1, txn_res1])
        self.assertGlobalStateContains(self.mock_response, value)
        self.assertGlobalStateContains(self.mock_response, value, txn_index=0)
        self.assertGlobalStateContains(self.mock_response, value, txn_index=1)

        self.mock_response = dict(error=None, txns=[txn_res1, txn_res2])
        self.assertGlobalStateContains(self.mock_response, value)
        self.assertGlobalStateContains(self.mock_response, value, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(
                self.mock_response, value, txn_index=1
            )

        self.mock_response = dict(error=None, txns=[txn_res2, txn_res2])
        with self.assertRaisesRegex(AssertionError, "not found in any of"):
            self.assertGlobalStateContains(self.mock_response, value)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(
                self.mock_response, value, txn_index=0
            )
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(
                self.mock_response, value, txn_index=1
            )

    def test_local_state(self):
        txn_res1 = {
            "local-deltas": [
                dict(
                    address="some_addr",
                    delta=[
                        dict(
                            key="test",
                            value=dict(action=1, uint=2),
                        )
                    ],
                )
            ]
        }
        txn_res2 = {
            "local-deltas": [
                dict(
                    address="some_addr",
                    delta=[
                        dict(
                            key="key",
                            value=dict(action=1, uint=2),
                        )
                    ],
                )
            ]
        }
        self.mock_response = dict(error=None, txns=[txn_res1])
        value = dict(key="test", value=dict(action=1, uint=2))
        self.assertLocalStateContains(
            "int 1", "some_addr", value, app=dict(on_complete=0)
        )

        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(
                "int 1", "other_addr", value, app=dict(on_complete=0)
            )

        value = dict(key="test", value=dict(action=1, uint=3))
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(
                "int 1", "other_addr", value, app=dict(on_complete=0)
            )

        self.mock_response = dict(error=None, txns=[txn_res1, txn_res1])
        value = dict(key="test", value=dict(action=1, uint=2))
        self.assertLocalStateContains(self.mock_response, "some_addr", value)
        self.assertLocalStateContains(
            self.mock_response, "some_addr", value, txn_index=0
        )
        self.assertLocalStateContains(
            self.mock_response, "some_addr", value, txn_index=1
        )

        self.mock_response = dict(error=None, txns=[txn_res2, txn_res1])
        self.assertLocalStateContains(self.mock_response, "some_addr", value)
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(
                self.mock_response, "some_addr", value, txn_index=0
            )
        self.assertLocalStateContains(
            self.mock_response, "some_addr", value, txn_index=1
        )

        self.mock_response = dict(error=None, txns=[txn_res2, txn_res2])
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(
                self.mock_response, "some_addr", value
            )
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(
                self.mock_response, "some_addr", value, txn_index=0
            )
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(
                self.mock_response, "some_addr", value, txn_index=1
            )
