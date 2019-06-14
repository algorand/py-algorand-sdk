from nacl.signing import SigningKey, VerifyKey
import base64
import encoding
import transaction
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

txidPrefix = bytes("TX", "ASCII")
checkSumLenBytes = 4

def signTransaction(txn, private_key):
    """
    Given a Transaction object and private key, returns the signed transaction.
    """
    # input txn as Transaction obj
    # input private_key as string from exportKey
    temp = txn
    private_key = base64.b64decode(bytes(private_key, "ascii"))
    txn = encoding.msgpack_encode(txn)
    to_sign = txidPrefix + base64.b64decode(bytes(txn, "ascii"))
    signing_key = SigningKey(private_key[:32])
    signed = signing_key.sign(to_sign)
    sig = signed.signature
    # msg = signed.message
    stx = transaction.SignedTransaction(temp, signature=sig)
    stxbytes = encoding.msgpack_encode(stx)
    txidbytes = hashes.Hash(hashes.SHA512_256(), default_backend())
    txidbytes.update(to_sign)
    txid = txidbytes.finalize()
    txid = base64.b32encode(txid).decode()
    sig = base64.b64encode(sig)
    sig = sig.decode()
    return stxbytes, txid, sig


def getTxid(txn):
    """
    Given a Transaction object, returns its transaction ID.
    """
    txn = encoding.msgpack_encode(txn)
    to_sign = txidPrefix + base64.b64decode(bytes(txn, "ascii"))
    txidbytes = hashes.Hash(hashes.SHA512_256(), default_backend())
    txidbytes.update(to_sign)
    txid = txidbytes.finalize()
    txid = base64.b32encode(txid).decode()
    return txid


def generateAccount():
    """
    Returns a SigningKey, VerifyKey, and string address.
    """
    sk = SigningKey.generate()
    vk = sk.verify_key
    hash = hashes.Hash(hashes.SHA512_256(), default_backend())
    hash.update(vk.encode())
    chksum = hash.finalize()
    print(chksum)
    a = vk.encode() + chksum[-checkSumLenBytes:]
    a = base64.b32encode(a).decode()
    return sk, vk, encoding.undo_padding(a)

