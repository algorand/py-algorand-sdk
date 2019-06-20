import base64
import umsgpack
from collections import OrderedDict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import transaction
import error

checkSumLenBytes = 4


def msgpack_encode(obj):
    """
    Encodes the object using canonical msgpack.
    
    Parameters
    ----------
    obj: Transaction, SignedTransaction, Multisig, Bid, or SignedBid

    Returns
    -------
    string: msgpack encoded obj
        
    Canonical Msgpack
    -----------------
    Maps must contain keys in lexicographic order;

    Maps must omit key-value pairs where the value is a zero-value;

    Positive integer values must be encoded as "unsigned" in msgpack, regardless of whether the value space is semantically signed or unsigned;

    Integer values must be represented in the shortest possible encoding;

    Binary arrays must be represented using the "bin" format family (that is, use the most recent version of msgpack rather than the older msgpack version that had no "bin" family).
    """
    if not isinstance(obj, dict):
        obj = obj.dictify()
    od = OrderedDict()
    for key in obj:
        if obj[key]:
            od[key] = obj[key]
    return base64.b64encode(umsgpack.dumps(od)).decode()


def msgpack_decode(enc):
    """
    Decodes a msgpack encoded object from a string.

    Parameters
    ----------
    enc: string

    Returns
    -------
    Transaction, SignedTransaction, Multisig, Bid, or SignedBid: enc decoded
    """
    decoded = umsgpack.loads(base64.b64decode(enc))
    if "type" in decoded:
        if decoded["type"].__eq__("pay"):
            return transaction.PaymentTxn.undictify(decoded)
        else:
            return transaction.KeyregTxn.undictify(decoded)
    if "txn" in decoded:
        return transaction.SignedTransaction.undictify(decoded)
    if "subsig" in decoded:
        return transaction.Multisig.undictify(decoded)


def isValidAddress(addr):
    """
    Checks if the string address is a valid Algorand address.

    Parameters
    ----------
    addr: string

    Returns
    -------
    boolean: whether or not the address is valid
    """
    if not isinstance(addr, str):
        return False
    if not len(undo_padding(addr)) == 58:
        return False
    try:
        decoded = decodeAddress(addr)
        if isinstance(decoded, str):
            return False
        return True
    except:
        return False


def decodeAddress(addr):
    """
    Decodes a string address into its address bytes and checksum.

    Parameters
    ----------
    addr: string

    Returns
    -------
    byte[]: address decoded into bytes

    """
    if not addr:
        return addr
    if not len(addr) == 58:
        raise error.WrongKeyLengthError
    decoded = base64.b32decode(correct_padding(addr))
    addr = decoded[:-checkSumLenBytes]
    expectedChksum = decoded[-checkSumLenBytes:]
    chksum = checksum(addr)
    
    if chksum.__eq__(expectedChksum):
        return addr
    else:
        raise error.WrongChecksumError


def encodeAddress(addrBytes):
    """
    Encodes a byte address into a string composed of the encoded bytes and the checksum.

    Parameters
    ----------
    addrBytes: byte[]

    Returns
    -------
    string: base32 encoded address
    """
    if not addrBytes:
        return addrBytes
    if not len(addrBytes) == 32:
        raise error.WrongKeyBytesLengthError
    chksum = checksum(addrBytes)
    addr = base64.b32encode(addrBytes+chksum)
    return undo_padding(addr.decode())


def checksum(addr):
    """
    Returns the checksum of size checkSumLenBytes for the address.

    Parameters
    ----------
    addr: byte[]

    Returns:
    byte[]: checksum of the address
    """
    hash = hashes.Hash(hashes.SHA512_256(), default_backend())
    hash.update(addr)
    chksum = hash.finalize()[-checkSumLenBytes:]
    return chksum


def correct_padding(a):
    if len(a)%8 == 0:
        return a
    return a + "="*(8-len(a)%8)


def undo_padding(a):
    return a.strip("=")
