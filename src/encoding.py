import base64  # (may not need if just using x.decode*)
import umsgpack
from collections import OrderedDict
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

checkSumLenBytes = 4


def msgpack_encode(obj):
    """
    Encodes the object using canonical msgpack (specified as follows) so that it is ready broadcast or sign.
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


def isValidAddress(addr):
    """
    Checks if the string address is valid.
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
    Decodes a string address into its address bytes and checksum, then returns the bytes.
    """
    if not addr:
        return addr
    decoded = base64.b32decode(correct_padding(addr))
    addr = decoded[:-checkSumLenBytes]
    expectedChksum = decoded[-checkSumLenBytes:]
    chksum = checksum(addr)
    
    if chksum.__eq__(expectedChksum):
        return addr
    else:
        return "wrong checksum"


def encodeAddress(addrBytes):
    """
    Encodes a byte address into a string composed of the bytes, encoded, and the checksum.
    """
    chksum = checksum(addrBytes)
    addr = base64.b32encode(addrBytes+chksum)
    return undo_padding(addr.decode())


def checksum(addr):
    """
    Returns the checksum of size checkSumLenBytes for the address.
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
