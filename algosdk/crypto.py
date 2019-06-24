from nacl.signing import SigningKey, VerifyKey
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from . import auction
from . import error
from . import encoding
from . import transaction

txidPrefix = bytes("TX", "ascii")
bidPrefix = bytes("aB", "ascii")
checkSumLenBytes = 4

def signTransaction(txn, private_key):
    """
    Signs a transaction with a private key.
    
    Parameters
    ----------
    txn: Transaction

    private_key: string

    Returns
    -------
    SignedTransaction: signed transaction with the signature

    string: transaction ID

    string: base64 encoded signature
    """
    sig = rawSignTransaction(txn, private_key)
    sig = base64.b64encode(sig).decode()
    stx = transaction.SignedTransaction(txn, signature=sig)
    txid = getTxid(txn)
    return stx, txid, sig

def rawSignTransaction(txn, private_key): 
    """
    Parameters
    ----------
    txn: Transaction

    private_key: string

    Returns
    -------
    byte[]: signature
    """
    private_key = base64.b64decode(bytes(private_key, "ascii"))
    txn = encoding.msgpack_encode(txn)
    to_sign = txidPrefix + base64.b64decode(bytes(txn, "ascii"))
    signing_key = SigningKey(private_key[:32])
    signed = signing_key.sign(to_sign)
    sig = signed.signature
    return sig



# to sign another transaction, you can either overwrite the signatures in the 
# current Multisig, or you can use Multisig.getAccountFromMultisig() to get
# a new multisig object with the same addresses
def signMultisigTransaction(private_key, preStx):
    """
    Signs a multisig transaction.
    
    Parameters
    ----------
    private_key: string

    preStx: SignedTransaction
        the multisig in the signed transaction can be partially 
        or fully signed; new signature will replace old if there 
        is already a signature for the address

    Returns
    -------
    SignedTransaction: signed transaction with multisig
    """
    err = preStx.multisig.validate()
    if err:
        return err
    addr = preStx.multisig.address()
    if not encoding.encodeAddress(preStx.transaction.sender) == addr:
        raise error.BadTxnSenderError
    index = -1
    public_key = base64.b64decode(bytes(private_key, "ascii"))[32:]
    for s in range(len(preStx.multisig.subsigs)):
        if preStx.multisig.subsigs[s].public_key == public_key:
            index = s
            break
    if index == -1:
        raise error.InvalidSecretKeyError
    sig = rawSignTransaction(preStx.transaction, private_key)
    preStx.multisig.subsigs[index].signature = sig
    return preStx

# only use if you are given two partially signed multisig transactions;
# to append a signature to a multisig transaction, just use signMultisigTransaction()
def mergeMultisigTransactions(partStxs):
    """
    Merges partially signed multisig transactions.

    Parameters
    ----------
    partStxs: SignedTransaction[]

    Returns
    -------
    SignedTransaction: signed transaction with the signature

    string: transaction ID
    """
    if len(partStxs) < 2:
        return "tried to merge less than two multisig transactions"
    # check that multisig parameters match
    refAddr = None
    refTxn = None
    for stx in partStxs:
        if not refAddr:
            refAddr = stx.multisig.address()
            refTxn = stx.transaction
        elif not stx.multisig.address() == refAddr:
                raise error.MergeKeysMismatchError
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
                        raise error.DuplicateSigMismatchError
    txid = getTxid(refTxn)
    return msigstx, txid


def signBid(bid, private_key): 
    """
    Signs a bid.

    Parameters
    ----------
    txn: Bid

    private_key: string

    Returns
    -------
    SignedBid: signed bid with the signature
    """
    temp = encoding.msgpack_encode(bid)
    to_sign = bidPrefix + base64.b64decode(bytes(temp, "ascii"))
    private_key = base64.b64decode(bytes(private_key, "ascii"))
    signing_key = SigningKey(private_key[:32])
    signed = signing_key.sign(to_sign)
    sig = signed.signature
    signed = auction.SignedBid(bid, base64.b64encode(sig))
    return signed


def getTxid(txn):
    """
    Returns a transaction's ID.

    Parameters
    ----------
    txn: Transaction

    Returns
    -------
    string: transaction ID
    """
    txn = encoding.msgpack_encode(txn)
    to_sign = txidPrefix + base64.b64decode(bytes(txn, "ascii"))
    txidbytes = hashes.Hash(hashes.SHA512_256(), default_backend())
    txidbytes.update(to_sign)
    txid = txidbytes.finalize()
    txid = base64.b32encode(txid).decode()
    return encoding.undo_padding(txid)


def generateAccount():
    """
    Generates an account.

    Returns
    -------
    string: private key

    string: account address
    """
    sk = SigningKey.generate()
    vk = sk.verify_key
    a = encoding.encodeAddress(vk.encode())
    private_key = base64.b64encode(sk.encode() + vk.encode()).decode()
    return private_key, encoding.undo_padding(a)


