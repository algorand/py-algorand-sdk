import unittest
from unittest.mock import MagicMock

from algosdk.wallet import Wallet


class TestWalletDeleteKey(unittest.TestCase):
    def _wallet_with_keys(self, addresses):
        kcl = MagicMock()
        kcl.list_wallets.return_value = [{"name": "w", "id": "id-1"}]
        kcl.init_wallet_handle.return_value = "handle-1"
        kcl.list_keys.return_value = list(addresses)
        kcl.delete_key.return_value = True
        # bypass __init__ side effects by constructing then overwriting
        wallet = Wallet.__new__(Wallet)
        wallet.name = "w"
        wallet.pswd = "p"
        wallet.kcl = kcl
        wallet.id = "id-1"
        wallet.handle = "handle-1"
        wallet.automate_handle = MagicMock()
        return wallet, kcl

    def test_delete_key_returns_false_when_address_missing(self):
        wallet, kcl = self._wallet_with_keys(["ADDR_A"])
        self.assertFalse(wallet.delete_key("ADDR_MISSING"))
        kcl.delete_key.assert_not_called()

    def test_delete_key_returns_true_when_address_present(self):
        wallet, kcl = self._wallet_with_keys(["ADDR_A", "ADDR_B"])
        self.assertTrue(wallet.delete_key("ADDR_B"))
        kcl.delete_key.assert_called_once_with("handle-1", "p", "ADDR_B")


if __name__ == "__main__":
    unittest.main()
