import base64
import unittest
import os
from pathlib import Path

import pytest

from algosdk import kmd
from algosdk.future import transaction
from algosdk import encoding
from algosdk import algod
from algosdk import account
from algosdk import mnemonic
from algosdk import error
from algosdk import auction
from algosdk import constants
from algosdk import wallet

from examples import tokens

wallet_name = "unencrypted-default-wallet"
wallet_pswd = ""


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)
        cls.kcl = kmd.KMDClient(tokens.kmd_token, tokens.kmd_address)
        w = wallet.Wallet(wallet_name, wallet_pswd, cls.kcl)
        keys = w.list_keys()
        max_balance = 0
        cls.account_0 = ""
        for k in keys:
            account_info = cls.acl.account_info(k)
            if account_info["amount"] > max_balance:
                max_balance = account_info["amount"]
                cls.account_0 = k

    def test_auction(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w["name"] == wallet_name:
                wallet_id = w["id"]

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # generate account with kmd
        account_1 = self.kcl.generate_key(handle, False)

        # get self.account_0 private key
        private_key_0 = self.kcl.export_key(
            handle, wallet_pswd, self.account_0
        )

        # create bid
        bid = auction.Bid(
            self.account_0, 10000, 260, "bid_id", account_1, "auc_id"
        )
        sb = bid.sign(private_key_0)
        nf = auction.NoteField(sb, constants.note_field_type_bid)

        # get suggested parameters and fee
        gh = self.acl.versions()["genesis_hash_b64"]
        rnd = int(self.acl.status()["lastRound"])
        sp = transaction.SuggestedParams(0, rnd, rnd + 100, gh)

        # create transaction
        txn = transaction.PaymentTxn(
            self.account_0,
            sp,
            account_1,
            100000,
            note=base64.b64decode(encoding.msgpack_encode(nf)),
        )

        # sign transaction with account
        signed_account = txn.sign(private_key_0)

        # send transaction
        send = self.acl.send_transaction(signed_account)
        self.assertEqual(send, txn.get_txid())
        del_1 = self.kcl.delete_key(handle, wallet_pswd, account_1)
        self.assertTrue(del_1)

    def test_handle(self):
        # create wallet; should raise error since wallet already exists
        self.assertRaises(
            error.KMDHTTPError,
            self.kcl.create_wallet,
            wallet_name,
            wallet_pswd,
        )

        # get the wallet ID
        wallets = self.kcl.list_wallets()

        wallet_id = None
        for w in wallets:
            if w["name"] == wallet_name:
                wallet_id = w["id"]

        # rename wallet
        self.assertEqual(
            wallet_name + "newname",
            self.kcl.rename_wallet(
                wallet_id, wallet_pswd, wallet_name + "newname"
            )["name"],
        )

        # change it back
        self.assertEqual(
            wallet_name,
            self.kcl.rename_wallet(wallet_id, wallet_pswd, wallet_name)[
                "name"
            ],
        )

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # get wallet
        self.assertIn("expires_seconds", self.kcl.get_wallet(handle))

        # renew the handle
        renewed_handle = self.kcl.renew_wallet_handle(handle)
        self.assertIn("expires_seconds", renewed_handle)

        # release the handle
        released = self.kcl.release_wallet_handle(handle)
        self.assertTrue(released)

        # check that the handle has been released
        self.assertRaises(error.KMDHTTPError, self.kcl.get_wallet, handle)

    @pytest.mark.skip(
        "skipping for now pending further investigation into failure (3/23/2022 - @tzaffi)"
    )
    def test_transaction(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w["name"] == wallet_name:
                wallet_id = w["id"]

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # generate account and check if it's valid
        private_key_1, account_1 = account.generate_account()
        self.assertTrue(encoding.is_valid_address(account_1))

        # import generated account
        import_key = self.kcl.import_key(handle, private_key_1)
        self.assertEqual(import_key, account_1)

        # generate account with kmd
        account_2 = self.kcl.generate_key(handle, False)

        # get suggested parameters and fee
        gh = self.acl.versions()["genesis_hash_b64"]
        rnd = int(self.acl.status()["lastRound"])
        sp = transaction.SuggestedParams(0, rnd, rnd + 100, gh)

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, sp, account_1, 100000)

        # sign transaction with kmd
        signed_kmd = self.kcl.sign_transaction(handle, wallet_pswd, txn)

        # get self.account_0 private key
        private_key_0 = self.kcl.export_key(
            handle, wallet_pswd, self.account_0
        )
        # sign transaction with account
        signed_account = txn.sign(private_key_0)
        txid = txn.get_txid()

        # check that signing both ways results in the same thing
        self.assertEqual(
            encoding.msgpack_encode(signed_account),
            encoding.msgpack_encode(signed_kmd),
        )

        # send the transaction
        send = self.acl.send_transaction(signed_account)
        self.assertEqual(send, txid)

        # get transaction info in pending transactions
        self.assertEqual(self.acl.pending_transaction_info(txid)["tx"], txid)

        # wait for transaction to send
        transaction.wait_for_confirmation(self.acl, txid, 10)

        # get transaction info two different ways
        info_1 = self.acl.transactions_by_address(
            self.account_0, sp.first - 2, sp.first + 2
        )
        info_2 = self.acl.transaction_info(self.account_0, txid)
        self.assertIn("transactions", info_1)
        self.assertIn("type", info_2)

        # delete accounts
        del_1 = self.kcl.delete_key(handle, wallet_pswd, account_1)
        del_2 = self.kcl.delete_key(handle, wallet_pswd, account_2)
        self.assertTrue(del_1)
        self.assertTrue(del_2)

    def test_multisig(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w["name"] == wallet_name:
                wallet_id = w["id"]

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # generate two accounts with kmd
        account_1 = self.kcl.generate_key(handle, False)
        account_2 = self.kcl.generate_key(handle, False)

        # get their private keys
        private_key_1 = self.kcl.export_key(handle, wallet_pswd, account_1)
        private_key_2 = self.kcl.export_key(handle, wallet_pswd, account_2)

        # get suggested parameters and fee
        gh = self.acl.versions()["genesis_hash_b64"]
        rnd = int(self.acl.status()["lastRound"])
        sp = transaction.SuggestedParams(0, rnd, rnd + 100, gh)

        # create multisig account and transaction
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        txn = transaction.PaymentTxn(msig.address(), sp, self.account_0, 1000)

        # check that the multisig account is valid
        msig.validate()

        # import multisig account
        msig_address = self.kcl.import_multisig(handle, msig)

        # export multisig account
        exported = self.kcl.export_multisig(handle, msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create multisig transaction
        mtx = transaction.MultisigTransaction(txn, msig)

        # sign using kmd
        msig_1 = self.kcl.sign_multisig_transaction(
            handle, wallet_pswd, account_1, mtx
        )
        signed_kmd = self.kcl.sign_multisig_transaction(
            handle, wallet_pswd, account_2, msig_1
        )

        # sign offline
        mtx1 = transaction.MultisigTransaction(txn, msig)
        mtx1.sign(private_key_1)
        mtx2 = transaction.MultisigTransaction(txn, msig)
        mtx2.sign(private_key_2)
        signed_account = transaction.MultisigTransaction.merge([mtx1, mtx2])

        # check that they are the same
        self.assertEqual(
            encoding.msgpack_encode(signed_account),
            encoding.msgpack_encode(signed_kmd),
        )

        # delete accounts
        del_1 = self.kcl.delete_key(handle, wallet_pswd, account_1)
        del_2 = self.kcl.delete_key(handle, wallet_pswd, account_2)
        del_3 = self.kcl.delete_multisig(handle, wallet_pswd, msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

    def test_wallet_info(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w["name"] == wallet_name:
                wallet_id = w["id"]

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # test listKeys
        list_keys = self.kcl.list_keys(handle)
        self.assertIn(self.account_0, list_keys)

        # test listMultisig
        list_multisig = self.kcl.list_multisig(handle)
        self.assertIsInstance(list_multisig, list)
        # either addresses are listed or there are no multisig accounts

        # test getting the master derivation key
        mdk = self.kcl.export_master_derivation_key(handle, wallet_pswd)
        self.assertIsInstance(mdk, str)

    def test_wallet(self):
        # initialize wallet
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)

        # get master derivation key
        mdk = w.export_master_derivation_key()

        # get mnemonic
        mn = w.get_mnemonic()

        # make sure mnemonic can be converted back to mdk
        self.assertEqual(mdk, mnemonic.to_master_derivation_key(mn))

        # generate account with account and check if it's valid
        private_key_1, account_1 = account.generate_account()

        # import generated account
        import_key = w.import_key(private_key_1)
        self.assertEqual(import_key, account_1)

        # check that the account is in the wallet
        keys = w.list_keys()
        self.assertIn(account_1, keys)

        # generate account with kmd
        account_2 = w.generate_key()
        private_key_2 = w.export_key(account_2)

        # get suggested parameters and fee
        gh = self.acl.versions()["genesis_hash_b64"]
        rnd = int(self.acl.status()["lastRound"])
        sp = transaction.SuggestedParams(0, rnd, rnd + 100, gh)

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, sp, account_1, 100000)

        # sign transaction with wallet
        signed_kmd = w.sign_transaction(txn)

        # get self.account_0 private key
        private_key_0 = w.export_key(self.account_0)

        # sign transaction with account
        signed_account = txn.sign(private_key_0)

        # check that signing both ways results in the same thing
        self.assertEqual(
            encoding.msgpack_encode(signed_account),
            encoding.msgpack_encode(signed_kmd),
        )

        # create multisig account and transaction
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        txn = transaction.PaymentTxn(msig.address(), sp, self.account_0, 1000)

        # import multisig account
        msig_address = w.import_multisig(msig)

        # check that the multisig account is listed
        msigs = w.list_multisig()
        self.assertIn(msig_address, msigs)

        # export multisig account
        exported = w.export_multisig(msig_address)
        self.assertEqual(len(exported.subsigs), 2)

        # create multisig transaction
        mtx = transaction.MultisigTransaction(txn, msig)

        # sign the multisig using kmd
        msig_1 = w.sign_multisig_transaction(account_1, mtx)
        signed_kmd = w.sign_multisig_transaction(account_2, msig_1)

        # sign the multisig offline
        mtx1 = transaction.MultisigTransaction(txn, msig)
        mtx1.sign(private_key_1)
        mtx2 = transaction.MultisigTransaction(txn, msig)
        mtx2.sign(private_key_2)
        signed_account = transaction.MultisigTransaction.merge([mtx1, mtx2])

        # check that they are the same
        self.assertEqual(
            encoding.msgpack_encode(signed_account),
            encoding.msgpack_encode(signed_kmd),
        )

        # delete accounts
        del_1 = w.delete_key(account_1)
        del_2 = w.delete_key(account_2)
        del_3 = w.delete_multisig(msig_address)
        self.assertTrue(del_1)
        self.assertTrue(del_2)
        self.assertTrue(del_3)

        # test renaming the wallet
        w.rename(wallet_name + "1")
        self.assertEqual(wallet_name + "1", w.info()["wallet"]["name"])
        w.rename(wallet_name)
        self.assertEqual(wallet_name, w.info()["wallet"]["name"])

        # test releasing the handle
        w.release_handle()
        self.assertRaises(error.KMDHTTPError, self.kcl.get_wallet, w.handle)

        # test handle automation
        w.info()

    def test_file_read_write(self):
        # get suggested parameters and fee
        gh = self.acl.versions()["genesis_hash_b64"]
        rnd = int(self.acl.status()["lastRound"])
        sp = transaction.SuggestedParams(0, rnd, rnd + 100, gh)

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, sp, self.account_0, 1000)

        # get private key
        w = wallet.Wallet(wallet_name, wallet_pswd, self.kcl)
        private_key = w.export_key(self.account_0)

        # sign transaction
        stx = txn.sign(private_key)

        # write to file
        raw_path = Path.cwd() / "raw.tx"
        transaction.write_to_file([txn, stx], raw_path)

        # read from file
        txns = transaction.retrieve_from_file(raw_path)

        # check that the transactions are still the same
        self.assertEqual(
            encoding.msgpack_encode(txn), encoding.msgpack_encode(txns[0])
        )
        self.assertEqual(
            encoding.msgpack_encode(stx), encoding.msgpack_encode(txns[1])
        )

        # delete the file
        os.remove(raw_path)

    def test_health(self):
        result = self.acl.health()
        self.assertEqual(result, None)

    @pytest.mark.skip(
        "skipping for now pending further investigation into failure (3/23/2022 - @tzaffi)"
    )
    def test_status_after_block(self):
        last_round = self.acl.status()["lastRound"]
        curr_round = self.acl.status_after_block(last_round)["lastRound"]
        self.assertEqual(last_round + 1, curr_round)

    def test_pending_transactions(self):
        result = self.acl.pending_transactions(0)
        self.assertIn("truncatedTxns", result)

    def test_algod_versions(self):
        result = self.acl.versions()
        self.assertIn("versions", result)

    def test_ledger_supply(self):
        result = self.acl.ledger_supply()
        self.assertIn("totalMoney", result)

    def test_block_info(self):
        last_round = self.acl.status()["lastRound"]
        result = self.acl.block_info(last_round)
        self.assertIn("hash", result)

    def test_kmd_versions(self):
        result = self.kcl.versions()
        self.assertIn("v1", result)

    def test_suggested_fee(self):
        result = self.acl.suggested_fee()
        self.assertIn("fee", result)

    def test_transaction_group(self):
        # get the default wallet
        wallets = self.kcl.list_wallets()
        wallet_id = None
        for w in wallets:
            if w["name"] == wallet_name:
                wallet_id = w["id"]

        # get a new handle for the wallet
        handle = self.kcl.init_wallet_handle(wallet_id, wallet_pswd)

        # get private key
        private_key_0 = self.kcl.export_key(
            handle, wallet_pswd, self.account_0
        )

        # get suggested parameters and fee
        gh = self.acl.versions()["genesis_hash_b64"]
        rnd = int(self.acl.status()["lastRound"])
        sp = transaction.SuggestedParams(0, rnd, rnd + 100, gh)

        # create transaction
        txn = transaction.PaymentTxn(self.account_0, sp, self.account_0, 1000)

        # calculate group id
        gid = transaction.calculate_group_id([txn])
        txn.group = gid

        # sign using kmd
        stxn1 = self.kcl.sign_transaction(handle, wallet_pswd, txn)
        # sign using transaction call
        stxn2 = txn.sign(private_key_0)
        # check that they are the same
        self.assertEqual(
            encoding.msgpack_encode(stxn1), encoding.msgpack_encode(stxn2)
        )

        try:
            send = self.acl.send_transactions([stxn1])
            self.assertEqual(send, txn.get_txid())
        except error.AlgodHTTPError as ex:
            self.assertNotIn('{"message"', str(ex))
            self.assertIn(
                "TransactionPool.Remember: transaction groups not supported",
                str(ex),
            )


if __name__ == "__main__":
    to_run = [TestIntegration]
    loader = unittest.TestLoader()
    suites = [
        loader.loadTestsFromTestCase(test_class) for test_class in to_run
    ]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)
