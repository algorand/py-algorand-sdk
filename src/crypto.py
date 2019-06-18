from nacl.signing import SigningKey, VerifyKey
import base64
import encoding
import transaction
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import umsgpack

txidPrefix = bytes("TX", "ASCII")
checkSumLenBytes = 4

def signTransaction(txn, private_key):
    """
    Given a Transaction object and private key (string), 
    returns the signed transaction, transaction ID, and the signature.
    """
    sig = rawSignTransaction(txn, private_key)
    stx = transaction.SignedTransaction(txn, signature=sig)
    stxstring = encoding.msgpack_encode(stx)
    sig = base64.b64encode(sig)
    sig = sig.decode()
    txid = getTxid(txn)
    return stxstring, txid, sig

def rawSignTransaction(txn, private_key): # obj, bytes
    """
    Given a Transaction object and a private key in bytes, 
    returns the signature in bytes.
    """
    private_key = base64.b64decode(bytes(private_key, "ascii"))
    txn = encoding.msgpack_encode(txn)
    to_sign = txidPrefix + base64.b64decode(bytes(txn, "ascii"))
    signing_key = SigningKey(private_key[:32])
    signed = signing_key.sign(to_sign)
    sig = signed.signature
    return sig


def signMultisigTransaction(txn, private_key, multisig):
    """
    Given a Transaction object, private key (string), and multisig, 
    signs the transaction and returns encoded multisig 
    that includes the additional signature.
    """
    err = multisig.validate()
    if err:
        return err
    addr = multisig.address()
    if not encoding.encodeAddress(txn.sender) == addr:
        return "bad transaction sender"
    index = -1
    public_key = base64.b64decode(bytes(private_key, "ascii"))[32:]
    for s in range(len(multisig.subsigs)):
        if multisig.subsigs[s].public_key == public_key:
            index = s
            break
    if index == -1:
        return "invalid secret key"
    sig = rawSignTransaction(txn, private_key)
    multisig.subsigs[index].signature = sig
    return encoding.msgpack_encode(multisig)


def appendMultisigTransaction(private_key, multisig, preStxBytes):
    """Adds a signature to a multisig transaction.
    prestxbytes is an encoded signed transaction
    multisig is obj"""
    stx = encoding.msgpack_decode(preStxBytes)
    msig = signMultisigTransaction(stx.transaction, private_key, multisig)
    msig = encoding.msgpack_decode(msig)
    partStx = transaction.SignedTransaction(stx.transaction, multisig=msig)
    partStx = encoding.msgpack_encode(partStx)
    return mergeMultisigTransactions([preStxBytes, partStx])
    

def mergeMultisigTransactions(partStxs):
    """Merges partially signed multisig transactions."""
    if len(partStxs) < 2:
        return "trying to merge less than two multisig transactions"
    partStxs = [encoding.msgpack_decode(s) for s in partStxs]
    # check that multisig parameters match
    refAddr = None
    refTxn = None
    for stx in partStxs:
        if not refAddr:
            refAddr = stx.multisig.address()
            refTxn = stx.transaction
        elif not stx.multisig.address() == refAddr:
                return "merge keys mismatch"
    msigstx = None
    for stx in partStxs:
        if not msigstx:
            msigstx = stx
        else:
            for s in range(len(stx.multisig.subsigs)):
                if stx.multisig.subsigs[s].signature:
                    if not msigstx.multisig.subsigs[s].signature:
                        msigstx.multisig.subsigs[s].signature = stx.multisig.subsigs[s].signature
                    elif not msigstx.multisig.subsigs[s].signature == stx.multisig.subsigs[s].signature:
                        return "mismatched duplicate signatures"
    stxbytes = encoding.msgpack_encode(msigstx)
    txid = getTxid(refTxn)
    return stxbytes, txid


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
    a = encoding.encodeAddress(vk.encode())
    return sk, vk, encoding.undo_padding(a)
