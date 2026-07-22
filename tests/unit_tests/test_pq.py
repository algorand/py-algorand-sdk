import base64
import copy
import json
import os
import unittest

import msgpack

from algosdk import constants, encoding, error, mnemonic, transaction
from algosdk.atomic_transaction_composer import LogicSigTransactionSigner
from algosdk.signer import Falcon1024TransactionSigner
from algosdk.transaction import LogicSigAccount, PQSig

DATA_DIR = os.path.join(os.path.dirname(__file__), "pq_test_data")


def _load(name):
    with open(os.path.join(DATA_DIR, name)) as f:
        return json.load(f)


class TestEd25519PointCheck(unittest.TestCase):
    def test_kat_vectors(self):
        """The broad point check must match every falcon-signatures KAT
        vector, including the small-order / non-canonical cases that a narrow
        (libsodium is_valid_point) predicate would get wrong."""
        kat = _load("lsig_address_kat.json")
        cases = []
        for c in kat["edwards25519_decode_cases"]:
            cases.append(
                (
                    c["encoding_hex"],
                    c["decodes_to_edwards25519_point"],
                    c["name"],
                )
            )
        for c in kat["lsig_derivation"]["counter_cases"]:
            cases.append(
                (
                    c["address_hex"],
                    c["decodes_to_edwards25519_point"],
                    "counter {}".format(c["counter"]),
                )
            )
        self.assertEqual(len(cases), 7)
        for hexval, expected, name in cases:
            self.assertEqual(
                encoding.is_ed25519_point(bytes.fromhex(hexval)),
                expected,
                "point check mismatch for {}".format(name),
            )

    def test_wrong_length_is_not_a_point(self):
        self.assertFalse(encoding.is_ed25519_point(b"\x00" * 31))
        self.assertFalse(encoding.is_ed25519_point(b"\x00" * 33))


class TestPQAddressDerivation(unittest.TestCase):
    def test_address_matches_go_algorand_fixture(self):
        fx = _load("pqMnemonic.json")
        pubkey = base64.b64decode(fx["publicKey"])
        address, salt = encoding.address_from_pq_key(
            constants.falcon_1024_scheme, pubkey
        )
        self.assertEqual(address, fx["address"])
        self.assertIsInstance(salt, int)
        self.assertTrue(0 <= salt <= 255)

    def test_derived_address_is_well_formed(self):
        # a PQ-derived address is a normal 58-char Algorand address that
        # round-trips through decode/encode
        pubkey = base64.b64decode(_load("pqMnemonic.json")["publicKey"])
        address, _ = encoding.address_from_pq_key(
            constants.falcon_1024_scheme, pubkey
        )
        self.assertEqual(len(address), 58)
        self.assertTrue(encoding.is_valid_address(address))
        self.assertEqual(
            encoding.encode_address(encoding.decode_address(address)),
            address,
        )

    def test_scheme_length_validation(self):
        for bad in [b"", b"x", b"xyz"]:
            with self.assertRaises(error.PQSchemeLengthError):
                encoding.address_from_pq_key(bad, b"\x00" * 32)

    def test_arbitrary_scheme_and_key_is_deterministic(self):
        # port of go-algorand's
        # TestCanonicalPQAddressSaltDoesNotRequireRegisteredSchemeOrValidatedKey:
        # derivation needs neither a registered scheme nor a validated key, and
        # is deterministic
        scheme, pubkey = b"x1", bytes([0xAB, 0xCD, 0xEF])
        address, salt = encoding.address_from_pq_key(scheme, pubkey)
        again, salt_again = encoding.address_from_pq_key(scheme, pubkey)
        self.assertEqual(address, again)
        self.assertEqual(salt, salt_again)

    def test_nonzero_salt_derivation_and_wire(self):
        scheme = constants.falcon_1024_scheme
        # search for a public key whose salt-0 candidate lands ON the curve,
        # forcing salt>0, so the rejection-sampling loop is exercised directly
        pk, salt = None, 0
        for i in range(1, 2000):
            candidate = i.to_bytes(32, "big")
            _, s = encoding.address_from_pq_key(scheme, candidate)
            if s > 0:
                pk, salt = candidate, s
                break
        self.assertIsNotNone(pk)
        self.assertGreater(salt, 0)
        # the chosen salt is genuinely the LOWEST off-curve salt
        for lower in range(salt):
            on = encoding.checksum(
                constants.pq_address_prefix + scheme + bytes([lower]) + pk
            )
            self.assertTrue(encoding.is_ed25519_point(on))
        off = encoding.checksum(
            constants.pq_address_prefix + scheme + bytes([salt]) + pk
        )
        self.assertFalse(encoding.is_ed25519_point(off))
        # end-to-end: the nonzero salt threads into the wire "slt" field
        txn = encoding.msgpack_decode(_load("pqPayment.json")["txnBlob"])
        signer = Falcon1024TransactionSigner(pk, lambda d: b"\x00" * 1280)
        self.assertEqual(signer.salt, salt)
        blob = encoding.msgpack_encode(signer.sign_transactions([txn], [0])[0])
        raw = msgpack.unpackb(base64.b64decode(blob), raw=False)
        self.assertEqual(raw["pqsig"]["slt"], salt)
        self.assertEqual(encoding.msgpack_decode(blob).pqsig.salt, salt)


class TestPQMnemonicSeed(unittest.TestCase):
    def test_seed_matches_go_algorand_fixture(self):
        fx = _load("pqMnemonic.json")
        seed = mnemonic.to_pq_seed(
            fx["mnemonic"], constants.falcon_1024_scheme
        )
        self.assertEqual(base64.b64encode(seed).decode(), fx["seed"])

    def test_scheme_length_validation(self):
        # to_pq_seed validates the scheme length just like address_from_pq_key
        fx = _load("pqMnemonic.json")
        for bad in [b"", b"x", b"xyz"]:
            with self.assertRaises(error.PQSchemeLengthError):
                mnemonic.to_pq_seed(fx["mnemonic"], bad)


class TestPQSigEncoding(unittest.TestCase):
    def test_roundtrip(self):
        pqsig = PQSig(b"f1", 3, b"pk-bytes", b"sig-bytes")
        self.assertEqual(PQSig.undictify(pqsig.dictify()), pqsig)

    def test_standalone_msgpack_roundtrip(self):
        # a bare PQSig (like a bare Multisig) must survive the generic
        # msgpack encode/decode path, despite carrying a "sig" key
        pqsig = PQSig(b"f1", 3, b"pk-bytes", b"sig-bytes")
        decoded = encoding.msgpack_decode(encoding.msgpack_encode(pqsig))
        self.assertIsInstance(decoded, PQSig)
        self.assertEqual(decoded, pqsig)

    def test_zero_salt_is_omitted(self):
        pqsig = PQSig(b"f1", 0, b"pk", b"sig")
        self.assertNotIn("slt", pqsig.dictify())
        # and it round-trips back to 0
        self.assertEqual(PQSig.undictify(pqsig.dictify()).salt, 0)


class TestPQTransactionSigner(unittest.TestCase):
    def _run(self, fixture_name):
        fx = _load(fixture_name)
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        expected_sig = base64.b64decode(fx["stxn"]["pqsig"]["sig"])
        txn = encoding.msgpack_decode(fx["txnBlob"])
        # sanity: the unsigned txn re-encodes to the fixture byte-for-byte
        self.assertEqual(encoding.msgpack_encode(txn), fx["txnBlob"])
        captured = {}

        def fake(to_sign):
            captured["to_sign"] = to_sign
            return expected_sig

        signer = Falcon1024TransactionSigner(pk, fake)
        stxn = signer.sign_transactions([txn], [0])[0]
        blob = encoding.msgpack_encode(stxn)
        return fx, stxn, blob, captured

    def test_direct_payment(self):
        fx, stxn, blob, captured = self._run("pqPayment.json")
        # the signed payload is the "TX"-prefixed transaction
        self.assertEqual(
            captured["to_sign"],
            stxn.transaction.bytes_to_sign(),
        )
        # byte-exact vs the go-algorand fixture
        expected = base64.b64decode(fx["stxnBlob"])
        self.assertEqual(base64.b64decode(blob), expected)
        self.assertIsNone(stxn.authorizing_address)
        # decode round-trip
        self.assertEqual(encoding.msgpack_decode(blob), stxn)

    def test_rekeyed_payment(self):
        fx, stxn, blob, captured = self._run("pqRekeyedPayment.json")
        expected = base64.b64decode(fx["stxnBlob"])
        self.assertEqual(base64.b64decode(blob), expected)
        self.assertEqual(stxn.authorizing_address, fx["stxn"]["sgnr"])
        self.assertEqual(encoding.msgpack_decode(blob), stxn)

    def test_signs_only_requested_indexes(self):
        fx = _load("pqPayment.json")
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        sig = base64.b64decode(fx["stxn"]["pqsig"]["sig"])
        base = encoding.msgpack_decode(fx["txnBlob"])
        t0, t1, t2 = (copy.deepcopy(base) for _ in range(3))
        t1.note, t2.note = b"1", b"2"
        signer = Falcon1024TransactionSigner(pk, lambda d: sig)
        stxns = signer.sign_transactions([t0, t1, t2], [0, 2])
        # only the requested indexes are signed, in order
        self.assertEqual(len(stxns), 2)
        self.assertEqual(stxns[0].transaction, t0)
        self.assertEqual(stxns[1].transaction, t2)
        self.assertNotEqual(stxns[1].transaction, t1)

    def test_honors_custom_scheme(self):
        # the generic PQTransactionSigner threads an arbitrary 2-byte scheme
        # into the wire signature (Falcon1024TransactionSigner fixes it to "f1")
        from algosdk.signer import PQTransactionSigner

        txn = encoding.msgpack_decode(_load("pqPayment.json")["txnBlob"])
        signer = PQTransactionSigner(
            bytes([0xAB, 0xCD, 0xEF]), lambda d: b"\x00" * 1280, b"x1"
        )
        self.assertEqual(signer.scheme, b"x1")
        stxn = signer.sign_transactions([txn], [0])[0]
        self.assertEqual(stxn.pqsig.scheme, b"x1")

    def test_write_retrieve_file_roundtrip(self):
        import tempfile

        from algosdk.transaction import (
            PQSignedTransaction,
            retrieve_from_file,
            write_to_file,
        )

        # rekeyed fixture carries an sgnr, so this also covers the auth
        # address surviving the file round-trip
        _, stxn, blob, _ = self._run("pqRekeyedPayment.json")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pq.tx")
            write_to_file([stxn], path)
            recovered = retrieve_from_file(path)
        self.assertEqual(len(recovered), 1)
        self.assertIsInstance(recovered[0], PQSignedTransaction)
        self.assertEqual(recovered[0], stxn)
        self.assertEqual(encoding.msgpack_encode(recovered[0]), blob)


class TestPQDelegatedLogicSig(unittest.TestCase):
    def _run(self, fixture_name):
        fx = _load(fixture_name)
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        program = base64.b64decode(fx["signer"]["lsig"])
        expected_sig = base64.b64decode(fx["stxn"]["lsig"]["pqsig"]["sig"])
        txn = encoding.msgpack_decode(fx["txnBlob"])
        captured = {}

        def fake(to_sign):
            captured["to_sign"] = to_sign
            return expected_sig

        lsig_acct = LogicSigAccount(program)
        Falcon1024TransactionSigner(pk, fake).sign_logicsig(lsig_acct)
        stxn = LogicSigTransactionSigner(lsig_acct).sign_transactions(
            [txn], [0]
        )[0]
        blob = encoding.msgpack_encode(stxn)
        return fx, stxn, blob, captured, lsig_acct

    def test_delegated_payment(self):
        fx, stxn, blob, captured, lsig_acct = self._run(
            "pqDelegatedPayment.json"
        )
        # the signed payload binds the delegating address to the program
        addr_bytes = encoding.decode_address(lsig_acct.address())
        self.assertEqual(
            captured["to_sign"],
            constants.pq_program_prefix + addr_bytes + lsig_acct.lsig.logic,
        )
        expected = base64.b64decode(fx["stxnBlob"])
        self.assertEqual(base64.b64decode(blob), expected)
        self.assertIsNone(stxn.auth_addr)
        self.assertEqual(encoding.msgpack_decode(blob), stxn)

    def test_rekeyed_delegated_payment(self):
        fx, stxn, blob, captured, lsig_acct = self._run(
            "pqRekeyedDelegatedPayment.json"
        )
        expected = base64.b64decode(fx["stxnBlob"])
        self.assertEqual(base64.b64decode(blob), expected)
        self.assertEqual(stxn.auth_addr, fx["stxn"]["sgnr"])
        self.assertEqual(encoding.msgpack_decode(blob), stxn)

    def test_pq_lsig_is_delegated_single_sig(self):
        fx = _load("pqDelegatedPayment.json")
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        program = base64.b64decode(fx["signer"]["lsig"])
        sig = base64.b64decode(fx["stxn"]["lsig"]["pqsig"]["sig"])
        lsig_acct = LogicSigAccount(program)
        Falcon1024TransactionSigner(pk, lambda d: sig).sign_logicsig(lsig_acct)
        self.assertTrue(lsig_acct.is_delegated())
        self.assertEqual(lsig_acct.sig_count(), 1)
        # the delegated address is the derived PQ address, not the escrow hash
        self.assertNotEqual(lsig_acct.address(), lsig_acct.lsig.address())

    def test_sign_pq_rejects_double_sign(self):
        fx = _load("pqDelegatedPayment.json")
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        sig = base64.b64decode(fx["stxn"]["lsig"]["pqsig"]["sig"])
        program = base64.b64decode(fx["signer"]["lsig"])
        lsig_acct = LogicSigAccount(program)
        signer = Falcon1024TransactionSigner(pk, lambda d: sig)
        signer.sign_logicsig(lsig_acct)
        with self.assertRaises(error.LogicSigOverspecifiedSignature):
            signer.sign_logicsig(lsig_acct)

    def test_pq_logicsig_verify(self):
        fx = _load("pqDelegatedPayment.json")
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        sig = base64.b64decode(fx["stxn"]["lsig"]["pqsig"]["sig"])
        program = base64.b64decode(fx["signer"]["lsig"])
        la = LogicSigAccount(program)
        Falcon1024TransactionSigner(pk, lambda d: sig).sign_logicsig(la)
        # verify() re-derives the delegating address from the PQ public key
        # and confirms it matches
        self.assertTrue(la.verify())
        # a mismatched delegating address must not verify
        self.assertFalse(la.lsig.verify(b"\x00" * 32))

    def test_decoding_tolerates_an_underivable_pq_address(self):
        # decoding does not derive the delegating address, so a scheme that
        # no address can be derived from still decodes for inspection
        for name, pick in [
            ("pqDelegatedPayment.json", lambda r: r["lsig"]["pqsig"]),
            ("pqPayment.json", lambda r: r["pqsig"]),
        ]:
            with self.subTest(name):
                fx = _load(name)
                raw = msgpack.unpackb(
                    base64.b64decode(fx["stxnBlob"]), raw=False
                )
                pick(raw)["sch"] = b"f123"
                blob = base64.b64encode(
                    msgpack.packb(raw, use_bin_type=True)
                ).decode()
                self.assertIsNotNone(encoding.msgpack_decode(blob))

    def test_sign_pq_then_ed25519_sign_rejected(self):
        # a post-quantum-signed logicsig must reject a subsequent ed25519
        # sign(), or the pqsig would be silently dropped on the wire
        from algosdk import account

        fx = _load("pqDelegatedPayment.json")
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        sig = base64.b64decode(fx["stxn"]["lsig"]["pqsig"]["sig"])
        program = base64.b64decode(fx["signer"]["lsig"])
        lsig_acct = LogicSigAccount(program)
        Falcon1024TransactionSigner(pk, lambda d: sig).sign_logicsig(lsig_acct)
        _, sk = account.generate_account()
        with self.assertRaises(error.LogicSigOverspecifiedSignature):
            lsig_acct.sign(sk)

    def test_logicsig_eq_distinguishes_pqsig(self):
        fx = _load("pqDelegatedPayment.json")
        pk = base64.b64decode(fx["signer"]["pqSigner"]["pk"])
        sig = base64.b64decode(fx["stxn"]["lsig"]["pqsig"]["sig"])
        program = base64.b64decode(fx["signer"]["lsig"])
        signed = LogicSigAccount(program)
        Falcon1024TransactionSigner(pk, lambda d: sig).sign_logicsig(signed)
        unsigned = LogicSigAccount(program)
        self.assertNotEqual(signed.lsig, unsigned.lsig)
        # a different post-quantum public key must not compare equal
        other = LogicSigAccount(program)
        Falcon1024TransactionSigner(
            bytes(reversed(pk)), lambda d: sig
        ).sign_logicsig(other)
        self.assertNotEqual(signed.lsig, other.lsig)


class TestPQFixtureDecode(unittest.TestCase):
    """Decoding a go-algorand fixture blob recovers the signature and
    re-encodes to the exact same bytes (wire key "pqsig")."""

    def test_decode_direct(self):
        from algosdk.transaction import PQSignedTransaction

        fx = _load("pqPayment.json")
        stxn = encoding.msgpack_decode(fx["stxnBlob"])
        self.assertIsInstance(stxn, PQSignedTransaction)
        self.assertEqual(
            base64.b64encode(stxn.pqsig.signature).decode(),
            fx["stxn"]["pqsig"]["sig"],
        )
        self.assertEqual(encoding.msgpack_encode(stxn), fx["stxnBlob"])

    def test_decode_delegated(self):
        fx = _load("pqDelegatedPayment.json")
        stxn = encoding.msgpack_decode(fx["stxnBlob"])
        self.assertIsNotNone(stxn.lsig.pqsig)
        self.assertEqual(
            base64.b64encode(stxn.lsig.pqsig.signature).decode(),
            fx["stxn"]["lsig"]["pqsig"]["sig"],
        )
        self.assertEqual(encoding.msgpack_encode(stxn), fx["stxnBlob"])


class TestPQPublicAPI(unittest.TestCase):
    """Guards the public import paths for the post-quantum surface. `make lint`
    does not catch a missing/renamed export, so assert every public name is
    reachable via its documented (submodule) path -- matching how the SDK
    exposes SignedTransaction, AccountTransactionSigner, etc."""

    def test_canonical_import_paths(self):
        from algosdk.transaction import PQSig, PQSignedTransaction
        from algosdk.encoding import address_from_pq_key, is_ed25519_point
        from algosdk.mnemonic import to_pq_seed
        from algosdk.signer import (
            Falcon1024TransactionSigner,
            PQTransactionSigner,
        )
        from algosdk.error import (
            NoCanonicalSaltError,
            PQMultisigUnsupportedError,
            PQSchemeLengthError,
        )

        self.assertTrue(callable(address_from_pq_key))
        self.assertTrue(callable(is_ed25519_point))
        self.assertTrue(callable(to_pq_seed))
        self.assertTrue(hasattr(PQSig, "dictify"))
        self.assertTrue(hasattr(PQSignedTransaction, "dictify"))
        self.assertTrue(
            hasattr(Falcon1024TransactionSigner, "sign_transactions")
        )
        self.assertTrue(hasattr(Falcon1024TransactionSigner, "sign_logicsig"))
        self.assertTrue(hasattr(PQTransactionSigner, "sign_transactions"))
        self.assertTrue(
            issubclass(Falcon1024TransactionSigner, PQTransactionSigner)
        )
        for exc in (
            NoCanonicalSaltError,
            PQMultisigUnsupportedError,
            PQSchemeLengthError,
        ):
            self.assertTrue(issubclass(exc, Exception))
        # pin the wire-format constants
        self.assertEqual(constants.falcon_1024_scheme, b"f1")
        self.assertEqual(constants.pqsig_key, "pqsig")
