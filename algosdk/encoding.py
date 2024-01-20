import base64
from collections import OrderedDict
from typing import Union

import msgpack
from Cryptodome.Hash import SHA512

from algosdk import auction, block, constants, error, transaction


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
        decoded = algo_msgp_decode(base64.b64decode(enc))
    return undictify(decoded)

def algo_msgp_decode(enc):
    """Performs msgpack decoding on an Algorand object.  Extra care is
    taken so that some internal fields that are marked as strings are
    decoded without utf-8 processing, because they aren't utf-8. Yet,
    we want most string like values to become Python str types for
    simplicity.

    """
    raw = msgpack.unpackb(enc, raw=True, strict_map_key=False)
    return cook(raw)

def cook(raw):
    stop = {b"gd", b"ld", b"lg"}
    safe = {b"type"}

    if isinstance(raw, dict):
        cooked = {}
        for key, value in raw.items():
            v = value if key in stop else cook(value)
            v = v.decode() if key in safe else v
            if type(key) is bytes:
                cooked[key.decode()] = v
            else:
                cooked[key] = v
        return cooked
    if isinstance(raw, list):
        return [cook(item) for item in raw]
    return raw

def undictify(d):
    if "type" in d:
        return transaction.Transaction.undictify(d)
    if "l" in d:
        return transaction.LogicSig.undictify(d)
    if "msig" in d:
        return transaction.MultisigTransaction.undictify(d)
    if "lsig" in d:
        if "txn" in d:
            return transaction.LogicSigTransaction.undictify(d)
        return transaction.LogicSigAccount.undictify(d)
    if "sig" in d:
        return transaction.SignedTransaction.undictify(d)
    if "gh" in d:               # must proceed next check, since `txn` is in header too, as txn root
        return block.Block.undictify(d)
    if "txn" in d:
        return transaction.Transaction.undictify(d["txn"])
    if "subsig" in d:
        return transaction.Multisig.undictify(d)
    if "txlist" in d:
        return transaction.TxGroup.undictify(d)
    if "t" in d:
        return auction.NoteField.undictify(d)
    if "bid" in d:
        return auction.SignedBid.undictify(d)
    if "auc" in d:
        return auction.Bid.undictify(d)
    if "block" in d:
        return block.BlockInfo.undictify(d)

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
