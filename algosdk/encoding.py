import base64
from collections import OrderedDict
from typing import Tuple, Union

import msgpack
from Cryptodome.Hash import SHA512

from algosdk import auction, constants, error, transaction


def msgpack_encode(obj):
    """
    Encode the object using canonical msgpack.

    Args:
        obj (Transaction, SignedTransaction, MultisigTransaction, Multisig,\
            Bid, or SignedBid): object to be encoded

    Returns:
        str: msgpack encoded object

    Note:
        Canonical Msgpack: maps must contain keys in lexicographic order; maps
        must omit key-value pairs where the value is a zero-value; positive
        integer values must be encoded as "unsigned" in msgpack, regardless of
        whether the value space is semantically signed or unsigned; integer
        values must be represented in the shortest possible encoding; binary
        arrays must be represented using the "bin" format family (that is, use
        the most recent version of msgpack rather than the older msgpack
        version that had no "bin" family).
    """
    d = obj
    if not isinstance(obj, dict):
        d = obj.dictify()
    od = _sort_dict(d)
    return base64.b64encode(msgpack.packb(od, use_bin_type=True)).decode()


def _sort_dict(d):
    """
    Sorts a dictionary recursively and removes all zero values.

    Args:
        d (dict): dictionary to be sorted

    Returns:
        OrderedDict: sorted dictionary with no zero values
    """
    od = OrderedDict()
    for k, v in sorted(d.items()):
        if isinstance(v, dict):
            od[k] = _sort_dict(v)
        elif v:
            od[k] = v
    return od


def msgpack_decode(enc):
    """
    Decode a msgpack encoded object from a string.

    Args:
        enc (str): string to be decoded

    Returns:
        Transaction, SignedTransaction, Multisig, Bid, or SignedBid:\
            decoded object
    """
    decoded = enc
    if not isinstance(enc, dict):
        decoded = msgpack.unpackb(base64.b64decode(enc), raw=False)
    if "type" in decoded:
        return transaction.Transaction.undictify(decoded)
    if "l" in decoded:
        return transaction.LogicSig.undictify(decoded)
    if "msig" in decoded:
        return transaction.MultisigTransaction.undictify(decoded)
    if "lsig" in decoded:
        if "txn" in decoded:
            return transaction.LogicSigTransaction.undictify(decoded)
        return transaction.LogicSigAccount.undictify(decoded)
    if "sch" in decoded:
        # A standalone PQSig also carries a "sig" key, so this check must
        # come before the SignedTransaction dispatch.
        return transaction.PQSig.undictify(decoded)
    if "sig" in decoded:
        return transaction.SignedTransaction.undictify(decoded)
    if constants.pqsig_key in decoded:
        return transaction.PQSignedTransaction.undictify(decoded)
    if "txn" in decoded:
        return transaction.Transaction.undictify(decoded["txn"])
    if "subsig" in decoded:
        return transaction.Multisig.undictify(decoded)
    if "txlist" in decoded:
        return transaction.TxGroup.undictify(decoded)
    if "t" in decoded:
        return auction.NoteField.undictify(decoded)
    if "bid" in decoded:
        return auction.SignedBid.undictify(decoded)
    if "auc" in decoded:
        return auction.Bid.undictify(decoded)


def is_valid_address(addr):
    """
    Check if the string address is a valid Algorand address.

    Args:
        addr (str): base32 address

    Returns:
        bool: whether or not the address is valid
    """
    if not isinstance(addr, str):
        return False
    if not len(_undo_padding(addr)) == constants.address_len:
        return False
    try:
        decoded = decode_address(addr)
        if isinstance(decoded, str):
            return False
        return True
    except:
        return False


def decode_address(addr):
    """
    Decode a string address into its address bytes and checksum.

    Args:
        addr (str): base32 address

    Returns:
        bytes: address decoded into bytes

    """
    if not addr:
        return addr
    if not len(addr) == constants.address_len:
        raise error.WrongKeyLengthError
    decoded = base64.b32decode(_correct_padding(addr))
    addr = decoded[: -constants.check_sum_len_bytes]
    expected_checksum = decoded[-constants.check_sum_len_bytes :]
    chksum = _checksum(addr)

    if chksum == expected_checksum:
        return addr
    else:
        raise error.WrongChecksumError


def encode_address(addr_bytes):
    """
    Encode a byte address into a string composed of the encoded bytes and the
    checksum.

    Args:
        addr_bytes (bytes): address in bytes

    Returns:
        str: base32 encoded address
    """
    if not addr_bytes:
        return addr_bytes
    if not len(addr_bytes) == constants.key_len_bytes:
        raise error.WrongKeyBytesLengthError
    chksum = _checksum(addr_bytes)
    addr = base64.b32encode(addr_bytes + chksum)
    return _undo_padding(addr.decode())


def _checksum(addr):
    """
    Compute the checksum of size checkSumLenBytes for the address.

    Args:
        addr (bytes): address in bytes

    Returns:
        bytes: checksum of the address
    """
    return checksum(addr)[-constants.check_sum_len_bytes :]


def _correct_padding(a):
    if len(a) % 8 == 0:
        return a
    return a + "=" * (8 - len(a) % 8)


def _undo_padding(a):
    return a.strip("=")


def checksum(data):
    """
    Compute the checksum of arbitrary binary input.

    Args:
        data (bytes): data as bytes

    Returns:
        bytes: checksum of the data
    """
    chksum = SHA512.new(truncate="256")
    chksum.update(data)
    return chksum.digest()


_ED25519_P = 2**255 - 19
_ED25519_D = (-121665 * pow(121666, _ED25519_P - 2, _ED25519_P)) % _ED25519_P


def is_ed25519_point(public_key: bytes) -> bool:
    """
    Check whether 32 bytes decode to any point on the ed25519 curve.

    This is the "broad" predicate used for post-quantum address derivation: it
    returns True if the value could be interpreted as a curve point by any
    ed25519 implementation, including small-order points, non-canonical
    encodings, and points outside the prime-order subgroup. It deliberately
    recognizes more encodings as curve points than libsodium's
    crypto_core_ed25519_is_valid_point, so address derivation rejects more
    candidate salts (matching go-algorand's basics.IsEdwards25519Point).

    Args:
        public_key (bytes): 32-byte value to test

    Returns:
        bool: True if the value decodes to an ed25519 point
    """
    if len(public_key) != constants.key_len_bytes:
        return False
    p = _ED25519_P
    # the low 255 bits are y; the top bit encodes the sign of x, ignored here
    y = (int.from_bytes(public_key, "little") & ((1 << 255) - 1)) % p
    u = (y * y - 1) % p
    v = (_ED25519_D * y * y + 1) % p
    # a point exists iff x^2 = u / v has a solution (u / v is a square)
    x = (u * pow(v, 3, p) * pow(u * pow(v, 7, p) % p, (p - 5) // 8, p)) % p
    vxx = (v * x * x) % p
    return vxx == u % p or vxx == (-u) % p


def address_from_pq_key(scheme: bytes, public_key: bytes) -> Tuple[str, int]:
    """
    Derive a post-quantum account address and its canonical salt.

    The address is SHA-512/256("PQA" + scheme + salt + public_key), where the
    canonical salt is the lowest byte value (0-255) whose resulting 32-byte
    digest does not decode to an ed25519 curve point.

    Args:
        scheme (bytes): 2-byte scheme identifier (e.g. b"f1" for Falcon-1024)
        public_key (bytes): the scheme's public key

    Returns:
        Tuple[str, int]: the derived address and its canonical salt
    """
    if len(scheme) != constants.pq_scheme_len:
        raise error.PQSchemeLengthError(len(scheme))
    for salt in range(256):
        candidate = checksum(
            constants.pq_address_prefix + scheme + bytes([salt]) + public_key
        )
        if not is_ed25519_point(candidate):
            return encode_address(candidate), salt
    raise error.NoCanonicalSaltError()


def encode_as_bytes(
    e: Union[bytes, bytearray, str, int]
) -> Union[bytes, bytearray]:
    """Confirm or coerce element to bytes."""
    if isinstance(e, (bytes, bytearray)):
        return e
    if isinstance(e, str):
        return e.encode()
    if isinstance(e, int):
        # Uses 8 bytes, big endian to match TEAL's btoi
        return e.to_bytes(8, "big")  # raises for negative or too big
    raise TypeError("{} is not bytes, bytearray, str, or int".format(e))
