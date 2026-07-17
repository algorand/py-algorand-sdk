import unittest
from unittest.mock import MagicMock

from algosdk import account, kmd, wallet


class TestWalletDeleteKey(unittest.TestCase):
    """Tests for Wallet.delete_key() return value fix.

    These tests verify that delete_key() returns False when the specified
    address does not exist in the wallet (bug fix for GitHub issue #472).
    """

    def _create_mock_wallet(self, existing_keys=None):
        """Create a wallet with a mocked KMD client."""
        if existing_keys is None:
            existing_keys = []

        # Create mock KMD client
        mock_kcl = MagicMock(spec=kmd.KMDClient)
        mock_kcl.list_keys.return_value = existing_keys
        mock_kcl.delete_key.return_value = True  # KMDClient returns True on success
        mock_kcl.list_wallets.return_value = [
            {"name": "test-wallet", "id": "test-id"}
        ]
        mock_kcl.create_wallet.return_value = {"id": "test-id"}
        mock_kcl.init_wallet_handle.return_value = "test-handle"
        mock_kcl.export_master_derivation_key.return_value = (
            "master-derivation-key"
        )

        # Create wallet with mocked client
        w = wallet.Wallet("test-wallet", "test-pass", mock_kcl)
        return w, mock_kcl


class TestWalletDeleteKeyExisting(TestWalletDeleteKey):
    """Happy path: deleting a key that exists should return True."""

    def test_delete_existing_key_returns_true(self):
        """delete_key should return True when key exists."""
        mock_address = "MOCKALICE1234567890ABCDEF"
        mock_wallet, mock_kcl = self._create_mock_wallet(
            existing_keys=[mock_address]
        )

        result = mock_wallet.delete_key(mock_address)

        self.assertTrue(result)
        # Verify kcl.delete_key was called
        mock_kcl.delete_key.assert_called_once()


class TestWalletDeleteKeyNonExistent(TestWalletDeleteKey):
    """Bug fix tests: deleting a non-existent key should return False."""

    def test_delete_non_existent_key_returns_false(self):
        """delete_key should return False when key does not exist."""
        mock_wallet, mock_kcl = self._create_mock_wallet(
            existing_keys=["ALICE1234567890ABCDEF"]
        )

        result = mock_wallet.delete_key("BOB1234567890ABCDEF")

        self.assertFalse(result)
        # Verify kcl.delete_key was NOT called (we short-circuit)
        mock_kcl.delete_key.assert_not_called()

    def test_delete_from_empty_wallet_returns_false(self):
        """delete_key should return False on an empty wallet."""
        mock_wallet, mock_kcl = self._create_mock_wallet(existing_keys=[])

        result = mock_wallet.delete_key("ANY_ADDRESS")

        self.assertFalse(result)
        mock_kcl.delete_key.assert_not_called()

    def test_delete_key_idempotent(self):
        """Calling delete_key twice on the same key should:
        first call returns True, second returns False."""
        mock_address = "MOCKALICE1234567890ABCDEF"
        mock_wallet, mock_kcl = self._create_mock_wallet(
            existing_keys=[mock_address]
        )

        first_result = mock_wallet.delete_key(mock_address)
        self.assertTrue(first_result)
        mock_kcl.delete_key.assert_called_once()

        # Second call should return False (key no longer exists)
        mock_kcl.delete_key.reset_mock()
        mock_kcl.list_keys.return_value = []  # Key was deleted

        second_result = mock_wallet.delete_key(mock_address)
        self.assertFalse(second_result)
        mock_kcl.delete_key.assert_not_called()


class TestWalletDeleteMultisig(unittest.TestCase):
    """Tests for Wallet.delete_multisig() return value fix."""

    def _create_mock_wallet(self, existing_multisig=None):
        """Create a wallet with a mocked KMD client."""
        mock_kcl = MagicMock(spec=kmd.KMDClient)
        mock_kcl.list_keys.return_value = []
        mock_kcl.list_multisig.return_value = (
            existing_multisig if existing_multisig else []
        )
        mock_kcl.delete_multisig.return_value = True  # KMDClient returns True on success
        mock_kcl.list_wallets.return_value = [
            {"name": "test-wallet", "id": "test-id"}
        ]
        mock_kcl.create_wallet.return_value = {"id": "test-id"}
        mock_kcl.init_wallet_handle.return_value = "test-handle"
        mock_kcl.export_master_derivation_key.return_value = (
            "master-derivation-key"
        )

        w = wallet.Wallet("test-wallet", "test-pass", mock_kcl)
        return w, mock_kcl

    def test_delete_non_existent_multisig_returns_false(self):
        """delete_multisig should return False when multisig does not exist."""
        mock_wallet, mock_kcl = self._create_mock_wallet(
            existing_multisig=["MSIG1234567890ABCDEF"]
        )

        result = mock_wallet.delete_multisig("MSIG000000000000000000")

        self.assertFalse(result)
        mock_kcl.delete_multisig.assert_not_called()

    def test_delete_from_empty_multisig_list_returns_false(self):
        """delete_multisig should return False on an empty wallet."""
        mock_wallet, mock_kcl = self._create_mock_wallet(existing_multisig=[])

        result = mock_wallet.delete_multisig("ANY_MSIG_ADDRESS")

        self.assertFalse(result)
        mock_kcl.delete_multisig.assert_not_called()


if __name__ == "__main__":
    unittest.main()
