"""
Callback-based signers.

These let a custom key backend (HD wallet, hardware device, KMS, ...) plug into
Algorand signing operations by supplying a single low-level callback that signs
exact bytes, instead of exposing a raw secret key.

`Ed25519TransactionSigner` and the post-quantum `PQTransactionSigner` (and its
Falcon-1024 specialization `Falcon1024TransactionSigner`) are all
`TransactionSigner`s (so they plug straight into an atomic transaction
composer) and delegate a logic signature in place via `sign_logicsig`.
`Ed25519TransactionSigner` additionally signs messages ("MX") and program
data; `Ed25519MultisigTransactionSigner` fills a multisig from several
ed25519 callback signers.

For signing a single transaction, pair any of these with
`algosdk.atomic_transaction_composer.sign_transaction_with_signer`.
"""

import base64
from typing import Callable, List, Optional

from algosdk import constants, encoding, error, transaction
from algosdk.atomic_transaction_composer import TransactionSigner
from algosdk.transaction import GenericSignedTransaction

__all__ = [
    "RawSigner",
    "Ed25519TransactionSigner",
    "Ed25519MultisigTransactionSigner",
    "PQTransactionSigner",
    "Falcon1024TransactionSigner",
]

# A low-level signing callback: signs the exact preimage bytes and returns the
# raw signature.
RawSigner = Callable[[bytes], bytes]


def _subsig_index(multisig: "transaction.Multisig", public_key: bytes) -> int:
    for i, subsig in enumerate(multisig.subsigs):
        if subsig.public_key == public_key:
            return i
    raise error.InvalidSecretKeyError


class Ed25519TransactionSigner(TransactionSigner):
    """
    A TransactionSigner backed by a single low-level ed25519 signing callback
    (a public key plus a function that signs exact bytes) instead of a raw
    secret key. Besides signing transactions it can also sign messages ("MX"),
    program data, and delegate logic signatures.

    Args:
        public_key (bytes): the 32-byte ed25519 public key
        signer (RawSigner): callback that signs exact preimage bytes and
            returns the raw 64-byte signature
    """

    def __init__(
        self,
        public_key: bytes,
        signer: RawSigner,
    ) -> None:
        super().__init__()
        self.public_key = public_key
        self.signer = signer
        self.address = encoding.encode_address(public_key)

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> List[GenericSignedTransaction]:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of signed transactions. The length of the array will
        be the same as the length of indexes, and each index i in the array
        corresponds to the signed transaction from txn_group[indexes[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction
                group that should be signed
        """
        stxns: List[GenericSignedTransaction] = []
        for i in indexes:
            txn = txn_group[i]
            sig = self.signer(txn.bytes_to_sign())
            # This signer's own address is the authorizer; attach it as the
            # auth address whenever the transaction is sent by a different
            # (rekeyed) account.
            auth = None if txn.sender == self.address else self.address
            stxns.append(
                transaction.SignedTransaction(
                    txn, base64.b64encode(sig).decode(), auth
                )
            )
        return stxns

    def sign_bytes(self, data: bytes) -> bytes:
        """Sign arbitrary bytes prefixed with "MX" (see util.sign_bytes)."""
        return self.signer(constants.bytes_prefix + data)

    def sign_program_data(
        self, data: bytes, lsig: "transaction.LogicSig"
    ) -> bytes:
        """
        Sign program data for the ed25519verify opcode (see logic.teal_sign):
        "ProgData" + lsig program address + data.
        """
        program_addr = encoding.decode_address(lsig.address())
        return self.signer(constants.logic_data_prefix + program_addr + data)

    def sign_logicsig(
        self,
        lsig_account: "transaction.LogicSigAccount",
        multisig: Optional["transaction.Multisig"] = None,
    ) -> None:
        """
        Delegate a LogicSigAccount to this signer, in place.

        Without `multisig` this signs "Program" + program and sets the
        single-key signature. With `multisig` it signs
        "MsigProgram" + multisig address + program and fills this signer's
        subsig in the delegating multisig.

        Args:
            lsig_account (LogicSigAccount): the account to delegate; mutated
            multisig (Multisig, optional): the delegating multisig account

        Raises:
            LogicSigOverspecifiedSignature: if the LogicSig is already signed
        """
        lsig = lsig_account.lsig
        if lsig.sig or lsig.msig or lsig.lmsig or lsig.pqsig:
            raise error.LogicSigOverspecifiedSignature
        if multisig is None:
            to_sign = constants.logic_prefix + lsig_account.lsig.logic
            sig = self.signer(to_sign)
            lsig_account.lsig.sig = base64.b64encode(sig).decode()
            lsig_account.sigkey = self.public_key
        else:
            index = _subsig_index(multisig, self.public_key)
            to_sign = (
                constants.multisig_logic_prefix
                + multisig.address_bytes()
                + lsig_account.lsig.logic
            )
            multisig.subsigs[index].signature = self.signer(to_sign)
            lsig_account.lsig.lmsig = multisig

    def append_to_logicsig_multisig(
        self, lsig_account: "transaction.LogicSigAccount"
    ) -> None:
        """
        Add this signer's subsig to an already multisig-delegated
        LogicSigAccount, in place.

        Use after `sign_logicsig(lsig_account, multisig)` has delegated the
        account to a multisig, to fill in each additional member's signature.
        This is the callback counterpart of
        `LogicSigAccount.append_to_multisig`.

        Args:
            lsig_account (LogicSigAccount): a multisig-delegated account;
                mutated

        Raises:
            InvalidSecretKeyError: if the account is not multisig-delegated, or
                this signer's public key is not a member of the delegating
                multisig
        """
        lmsig = lsig_account.lsig.lmsig
        if lmsig is None:
            raise error.InvalidSecretKeyError
        index = _subsig_index(lmsig, self.public_key)
        to_sign = (
            constants.multisig_logic_prefix
            + lmsig.address_bytes()
            + lsig_account.lsig.logic
        )
        lmsig.subsigs[index].signature = self.signer(to_sign)


class Ed25519MultisigTransactionSigner(TransactionSigner):
    """
    Multisig TransactionSigner that fills each member's subsig using an
    Ed25519TransactionSigner callback instead of a raw secret key.

    Args:
        msig (Multisig): the multisig account
        signers (List[Ed25519TransactionSigner]): the members to sign with;
            each must be a public key present in the multisig. Only each
            member's public key and signing callback are used.
    """

    def __init__(
        self,
        msig: "transaction.Multisig",
        signers: List[Ed25519TransactionSigner],
    ) -> None:
        super().__init__()
        self.msig = msig
        self.signers = signers

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> List[GenericSignedTransaction]:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of signed transactions. The length of the array will
        be the same as the length of indexes, and each index i in the array
        corresponds to the signed transaction from txn_group[indexes[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction
                group that should be signed
        """
        # Fail fast on a malformed multisig, matching the secret-key path
        # (MultisigTransaction.sign validates before signing).
        self.msig.validate()
        stxns: List[GenericSignedTransaction] = []
        for i in indexes:
            txn = txn_group[i]
            mtxn = transaction.MultisigTransaction(
                txn, self.msig.get_multisig_account()
            )
            for member in self.signers:
                index = _subsig_index(mtxn.multisig, member.public_key)
                mtxn.multisig.subsigs[index].signature = member.signer(
                    txn.bytes_to_sign()
                )
            stxns.append(mtxn)
        return stxns


class PQTransactionSigner(TransactionSigner):
    """
    A TransactionSigner backed by a post-quantum signing callback (a public key
    plus a function that signs a 32-byte digest) instead of a raw secret key,
    parameterized by a 2-byte scheme identifier. Besides signing transactions it
    can delegate a logic signature via `sign_logicsig`.

    For Falcon-1024 use the `Falcon1024TransactionSigner` subclass, which fixes
    the scheme for you.

    Args:
        public_key (bytes): the scheme's public key
        signer (RawSigner): callback that returns a raw post-quantum signature
            over the given 32-byte digest
        scheme (bytes): 2-byte scheme identifier (e.g. b"f1" for Falcon-1024)
    """

    def __init__(
        self,
        public_key: bytes,
        signer: RawSigner,
        scheme: bytes,
    ) -> None:
        super().__init__()
        self.public_key = public_key
        self.signer = signer
        self.scheme = scheme
        self.address, self.salt = encoding.address_from_pq_key(
            scheme, public_key
        )

    def sign_transactions(
        self, txn_group: List[transaction.Transaction], indexes: List[int]
    ) -> List[GenericSignedTransaction]:
        """
        Sign transactions in a transaction group given the indexes.

        Returns an array of signed transactions. The length of the array will
        be the same as the length of indexes, and each index i in the array
        corresponds to the signed transaction from txn_group[indexes[i]].

        Args:
            txn_group (list[Transaction]): atomic group of transactions
            indexes (list[int]): array of indexes in the atomic transaction
                group that should be signed
        """
        stxns: List[GenericSignedTransaction] = []
        for i in indexes:
            txn = txn_group[i]
            to_sign = encoding.checksum(txn.bytes_to_sign())
            sig = self.signer(to_sign)
            pqsig = transaction.PQSig(
                self.scheme, self.salt, self.public_key, sig
            )
            # The post-quantum address is the authorizer; attach it as the auth
            # address whenever the transaction is sent by a different (rekeyed)
            # account.
            auth = None if txn.sender == self.address else self.address
            stxn = transaction.PQSignedTransaction(txn, pqsig, auth)
            stxns.append(stxn)
        return stxns

    def sign_logicsig(
        self,
        lsig_account: "transaction.LogicSigAccount",
        multisig: Optional["transaction.Multisig"] = None,
    ) -> None:
        """
        Delegate a LogicSigAccount to this signer, in place, with a post-quantum
        signature. Signs "PQProgram" + post-quantum address + program.

        Args:
            lsig_account (LogicSigAccount): the account to delegate; mutated
            multisig (Multisig, optional): unsupported for post-quantum
                signatures; passing it raises PQMultisigUnsupportedError

        Raises:
            PQMultisigUnsupportedError: if a multisig is provided
            LogicSigOverspecifiedSignature: if the LogicSig is already signed
        """
        if multisig is not None:
            raise error.PQMultisigUnsupportedError
        lsig = lsig_account.lsig
        if lsig.sig or lsig.msig or lsig.lmsig or lsig.pqsig:
            raise error.LogicSigOverspecifiedSignature
        address_bytes = encoding.decode_address(self.address)
        to_sign = encoding.checksum(
            constants.pq_program_prefix + address_bytes + lsig.logic
        )
        sig = self.signer(to_sign)
        lsig.pqsig = transaction.PQSig(
            self.scheme, self.salt, self.public_key, sig
        )
        lsig_account.sigkey = address_bytes


class Falcon1024TransactionSigner(PQTransactionSigner):
    """
    A PQTransactionSigner specialized to the Falcon-1024 post-quantum signature
    scheme (`constants.falcon_1024_scheme`). This is the post-quantum signer to
    reach for.

    Args:
        public_key (bytes): the Falcon-1024 public key
        signer (RawSigner): callback that returns a raw Falcon-1024 signature
            over the given 32-byte digest
    """

    def __init__(
        self,
        public_key: bytes,
        signer: RawSigner,
    ) -> None:
        super().__init__(public_key, signer, constants.falcon_1024_scheme)
