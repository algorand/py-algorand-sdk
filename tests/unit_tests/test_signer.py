import base64
import unittest

from nacl.signing import SigningKey

from algosdk import (
    account,
    constants,
    encoding,
    error,
    logic,
    transaction,
    util,
)
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    MultisigTransactionSigner,
    sign_transaction_with_signer,
)
from algosdk.signer import (
    Ed25519MultisigTransactionSigner,
    Ed25519TransactionSigner,
    Falcon1024TransactionSigner,
)
from algosdk.transaction import LogicSigAccount, Multisig, PaymentTxn

GH = base64.b64encode(bytes(32)).decode()
PROGRAM = bytes([0x01, 0x20, 0x01, 0x01, 0x22])  # int 1


def _sp():
    return transaction.SuggestedParams(1000, 1, 1000, GH, flat_fee=True)


def _raw(sk):
    """A low-level ed25519 signer callback backed by a real secret key."""
    seed = base64.b64decode(sk)[: constants.key_len_bytes]
    signing_key = SigningKey(seed)
    return lambda data: signing_key.sign(data).signature


class TestEd25519TransactionSigner(unittest.TestCase):
    """Every callback signer must be byte-identical to the existing sk path."""

    def test_exposes_capabilities_and_default_address(self):
        sk, addr = account.generate_account()
        signer = Ed25519TransactionSigner(
            encoding.decode_address(addr), _raw(sk)
        )
        # the signer's address defaults to its public key's address
        self.assertEqual(signer.address, addr)
        # and it exposes the full ed25519 signer capability surface
        for method in (
            "sign_transactions",
            "sign_bytes",
            "sign_program_data",
            "sign_logicsig",
            "append_to_logicsig_multisig",
        ):
            self.assertTrue(callable(getattr(signer, method)))

    def test_transaction_signer_equivalence(self):
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        txn = PaymentTxn(addr, _sp(), addr, 1000)
        ref = AccountTransactionSigner(sk).sign_transactions([txn], [0])[0]
        got = Ed25519TransactionSigner(pk, _raw(sk)).sign_transactions(
            [txn], [0]
        )[0]
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )

    def test_signs_only_requested_indexes(self):
        # sign_transactions returns exactly the requested indexes, in order
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        txns = [PaymentTxn(addr, _sp(), addr, i) for i in range(3)]
        signed = Ed25519TransactionSigner(pk, _raw(sk)).sign_transactions(
            txns, [0, 2]
        )
        self.assertEqual(len(signed), 2)
        self.assertEqual(signed[0].transaction, txns[0])
        self.assertEqual(signed[1].transaction, txns[2])

    def test_transaction_signer_rekeyed_equivalence(self):
        # signer key differs from the txn sender (rekeyed account): the
        # signer's own address must be attached as the auth address
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        _, other = account.generate_account()
        txn = PaymentTxn(other, _sp(), other, 1000)
        ref = AccountTransactionSigner(sk).sign_transactions([txn], [0])[0]
        got = Ed25519TransactionSigner(pk, _raw(sk)).sign_transactions(
            [txn], [0]
        )[0]
        self.assertEqual(got.authorizing_address, addr)
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )

    def test_sign_bytes_equivalence(self):
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        data = b"a message to sign"
        got = Ed25519TransactionSigner(pk, _raw(sk)).sign_bytes(data)
        # drop-in replacement for util.sign_bytes: same base64 output,
        # verifies directly with util.verify_bytes
        self.assertEqual(got, util.sign_bytes(data, sk))
        self.assertTrue(util.verify_bytes(data, got, addr))

    def test_sign_bytes_does_not_verify_other_bytes(self):
        # negative check: the "MX" signature must not verify for other bytes
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        sig = Ed25519TransactionSigner(pk, _raw(sk)).sign_bytes(b"hello world")
        self.assertFalse(util.verify_bytes(b"goodbye world", sig, addr))

    def test_sign_program_data_equivalence(self):
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        lsig = transaction.LogicSig(PROGRAM)
        data = b"program data"
        ref = logic.teal_sign(sk, data, lsig.address())
        got = Ed25519TransactionSigner(pk, _raw(sk)).sign_program_data(
            data, lsig
        )
        self.assertEqual(got, ref)

    def test_sign_logicsig_single_equivalence(self):
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        ref = LogicSigAccount(PROGRAM)
        ref.sign(sk)
        got = LogicSigAccount(PROGRAM)
        Ed25519TransactionSigner(pk, _raw(sk)).sign_logicsig(got)
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )
        self.assertEqual(got.address(), ref.address())

    def test_sign_logicsig_rejects_double_sign(self):
        sk, addr = account.generate_account()
        pk = encoding.decode_address(addr)
        la = LogicSigAccount(PROGRAM)
        signer = Ed25519TransactionSigner(pk, _raw(sk))
        signer.sign_logicsig(la)
        with self.assertRaises(error.LogicSigOverspecifiedSignature):
            signer.sign_logicsig(la)

    def test_sign_logicsig_multisig_equivalence(self):
        sk1, a1 = account.generate_account()
        _, a2 = account.generate_account()
        _, a3 = account.generate_account()
        msig = Multisig(1, 2, [a1, a2, a3])
        ref = LogicSigAccount(PROGRAM)
        ref.sign_multisig(msig.get_multisig_account(), sk1)
        got = LogicSigAccount(PROGRAM)
        Ed25519TransactionSigner(
            encoding.decode_address(a1), _raw(sk1)
        ).sign_logicsig(got, msig.get_multisig_account())
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )

    def test_append_to_logicsig_multisig_equivalence(self):
        sk1, a1 = account.generate_account()
        sk2, a2 = account.generate_account()
        _, a3 = account.generate_account()
        msig = Multisig(1, 2, [a1, a2, a3])
        # secret-key reference: sign_multisig then append_to_multisig
        ref = LogicSigAccount(PROGRAM)
        ref.sign_multisig(msig.get_multisig_account(), sk1)
        ref.append_to_multisig(sk2)
        # callback path: sign_logicsig (first member) then
        # append_to_logicsig_multisig (each additional member)
        got = LogicSigAccount(PROGRAM)
        Ed25519TransactionSigner(
            encoding.decode_address(a1), _raw(sk1)
        ).sign_logicsig(got, msig.get_multisig_account())
        Ed25519TransactionSigner(
            encoding.decode_address(a2), _raw(sk2)
        ).append_to_logicsig_multisig(got)
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )
        self.assertEqual(got.address(), ref.address())
        self.assertTrue(got.verify())

    def test_append_to_logicsig_multisig_requires_delegation(self):
        sk1, a1 = account.generate_account()
        la = LogicSigAccount(PROGRAM)  # never delegated to a multisig
        with self.assertRaises(error.InvalidSecretKeyError):
            Ed25519TransactionSigner(
                encoding.decode_address(a1), _raw(sk1)
            ).append_to_logicsig_multisig(la)

    def test_append_to_logicsig_multisig_rejects_non_member(self):
        sk1, a1 = account.generate_account()
        _, a2 = account.generate_account()
        outsider_sk, outsider_addr = account.generate_account()
        msig = Multisig(1, 2, [a1, a2])
        la = LogicSigAccount(PROGRAM)
        Ed25519TransactionSigner(
            encoding.decode_address(a1), _raw(sk1)
        ).sign_logicsig(la, msig.get_multisig_account())
        with self.assertRaises(error.InvalidSecretKeyError):
            Ed25519TransactionSigner(
                encoding.decode_address(outsider_addr), _raw(outsider_sk)
            ).append_to_logicsig_multisig(la)


class TestEd25519MultisigTransactionSigner(unittest.TestCase):
    def test_equivalence_with_sk_signer(self):
        sk1, a1 = account.generate_account()
        sk2, a2 = account.generate_account()
        _, a3 = account.generate_account()
        msig = Multisig(1, 2, [a1, a2, a3])
        txn = PaymentTxn(msig.address(), _sp(), a1, 1000)
        ref = MultisigTransactionSigner(
            msig.get_multisig_account(), [sk1, sk2]
        ).sign_transactions([txn], [0])[0]
        signers = [
            Ed25519TransactionSigner(encoding.decode_address(a1), _raw(sk1)),
            Ed25519TransactionSigner(encoding.decode_address(a2), _raw(sk2)),
        ]
        got = Ed25519MultisigTransactionSigner(
            msig.get_multisig_account(), signers
        ).sign_transactions([txn], [0])[0]
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )

    def test_unknown_member_raises(self):
        _, a1 = account.generate_account()
        _, a2 = account.generate_account()
        outsider_sk, outsider_addr = account.generate_account()
        msig = Multisig(1, 1, [a1, a2])
        txn = PaymentTxn(msig.address(), _sp(), a1, 1000)
        signer = Ed25519TransactionSigner(
            encoding.decode_address(outsider_addr), _raw(outsider_sk)
        )
        with self.assertRaises(error.InvalidSecretKeyError):
            Ed25519MultisigTransactionSigner(
                msig.get_multisig_account(), [signer]
            ).sign_transactions([txn], [0])

    def test_rejects_malformed_multisig(self):
        # a malformed multisig fails fast, matching the secret-key path
        sk1, a1 = account.generate_account()
        bad = Multisig(1, 2, [a1])  # threshold 2 with a single member
        txn = PaymentTxn(a1, _sp(), a1, 1000)
        signer = Ed25519TransactionSigner(
            encoding.decode_address(a1), _raw(sk1)
        )
        with self.assertRaises(error.InvalidThresholdError):
            Ed25519MultisigTransactionSigner(
                bad.get_multisig_account(), [signer]
            ).sign_transactions([txn], [0])


class TestFalconMultisigRejection(unittest.TestCase):
    def test_sign_logicsig_rejects_multisig(self):
        _, a1 = account.generate_account()
        msig = Multisig(1, 1, [a1])
        la = LogicSigAccount(PROGRAM)
        signer = Falcon1024TransactionSigner(
            b"\x00" * 1793, lambda d: b"\x00" * 1280
        )
        with self.assertRaises(error.PQMultisigUnsupportedError):
            signer.sign_logicsig(la, multisig=msig)


class TestSignWithSigner(unittest.TestCase):
    """The account-driven sign_with_signer / append_to_multisig_with_signer
    (the signer-based replacements for the deprecated sk methods) match the
    secret-key path byte-for-byte."""

    def test_single(self):
        sk, a1 = account.generate_account()
        ref = LogicSigAccount(PROGRAM)
        ref.sign(sk)
        got = LogicSigAccount(PROGRAM)
        got.sign_with_signer(
            Ed25519TransactionSigner(encoding.decode_address(a1), _raw(sk))
        )
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )
        self.assertEqual(got.address(), ref.address())

    def test_multisig_and_append(self):
        sk1, a1 = account.generate_account()
        sk2, a2 = account.generate_account()
        _, a3 = account.generate_account()
        msig = Multisig(1, 2, [a1, a2, a3])
        ref = LogicSigAccount(PROGRAM)
        ref.sign_multisig(msig.get_multisig_account(), sk1)
        ref.append_to_multisig(sk2)
        got = LogicSigAccount(PROGRAM)
        got.sign_with_signer(
            Ed25519TransactionSigner(encoding.decode_address(a1), _raw(sk1)),
            msig.get_multisig_account(),
        )
        got.append_to_multisig_with_signer(
            Ed25519TransactionSigner(encoding.decode_address(a2), _raw(sk2))
        )
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )


class TestSignTransactionWithSigner(unittest.TestCase):
    """The single-transaction helper matches signing the txn directly and is
    the replacement for the deprecated Transaction.sign."""

    def test_equivalent_to_signer_and_deprecated_sign(self):
        sk, addr = account.generate_account()
        txn = PaymentTxn(addr, _sp(), addr, 1000)
        got = sign_transaction_with_signer(txn, AccountTransactionSigner(sk))
        # matches the verbose signer form...
        ref = AccountTransactionSigner(sk).sign_transactions([txn], [0])[0]
        self.assertEqual(
            encoding.msgpack_encode(got), encoding.msgpack_encode(ref)
        )
        # ...and the (deprecated) Transaction.sign it replaces
        self.assertEqual(
            encoding.msgpack_encode(got),
            encoding.msgpack_encode(txn.sign(sk)),
        )
