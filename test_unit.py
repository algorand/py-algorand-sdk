import sys
import unittest

from tests.unit_tests.test_abi import (
    TestABIEncoding,
    TestABIInteraction,
    TestABIType,
)
from tests.unit_tests.test_dryrun import TestDryrun
from tests.unit_tests.test_logicsig import (
    TestLogicSig,
    TestLogicSigAccount,
    TestLogicSigTransaction,
    TestMultisig,
)
from tests.unit_tests.test_other import (
    TestAddress,
    TestLogic,
    TestMnemonic,
    TestMsgpack,
    TestSignBytes,
)
from tests.unit_tests.test_transaction import (
    TestApplicationTransactions,
    TestAssetConfigConveniences,
    TestAssetTransferConveniences,
    TestPaymentTransaction,
)

if __name__ == "__main__":
    to_run = [
        TestPaymentTransaction,
        TestAssetConfigConveniences,
        TestAssetTransferConveniences,
        TestApplicationTransactions,
        TestMnemonic,
        TestAddress,
        TestMultisig,
        TestMsgpack,
        TestSignBytes,
        TestLogic,
        TestLogicSig,
        TestLogicSigAccount,
        TestLogicSigTransaction,
        TestDryrun,
        TestABIType,
        TestABIEncoding,
        TestABIInteraction,
    ]
    loader = unittest.TestLoader()
    suites = [
        loader.loadTestsFromTestCase(test_class) for test_class in to_run
    ]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)
    ret = not results.wasSuccessful()
    sys.exit(ret)
