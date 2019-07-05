from nacl.signing import SigningKey
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from . import auction
from . import error
from . import encoding
from . import transaction
from . import constants


def sign_transaction(txn, private_key):
    """
    Sign a transaction with a private key.

    Args:
        txn (Transaction): the transaction to be signed
        private_key (str): the private key of the signing account

    Returns:
        (SignedTransaction, str, str): signed transaction with the signature,
            transaction ID, base64 encoded signature
    """
    sig = raw_sign_transaction(txn, private_key)
    sig = base64.b64encode(sig).decode()
    stx = transaction.SignedTransaction(txn, signature=sig)
    txid = get_txid(txn)
    return stx, txid, sig


def raw_sign_transaction(txn, private_key):
    """
    Sign a transaction.

    Args:
        txn (Transaction): the transaction to be signed
        private_key (str): the private key of the signing account

    Returns:
        bytes: signature
    """
    private_key = base64.b64decode(bytes(private_key, "ascii"))
    txn = encoding.msgpack_encode(txn)
    to_sign = constants.txid_prefix + base64.b64decode(bytes(txn, "ascii"))
    signing_key = SigningKey(private_key[:32])
    signed = signing_key.sign(to_sign)
    sig = signed.signature
    return sig


def sign_multisig_transaction(private_key, pre_stx):
    """
    Sign a multisig transaction.

    Args:
        private_key (str): private key of signing account
        pre_stx (SignedTransaction): object containing unsigned or partially
            signed multisig

    Returns:
        SignedTransaction: signed transaction with multisig containing
            signature

    Note:
        The multisig in the pre_stx can be partially or fully signed; a new
        signature will replace the old if there is already a signature for the
        address. To sign another transaction, you can either overwrite the
        signatures in the current Multisig, or you can use
        Multisig.get_account_from_multisig() to get a new multisig object with
        the same addresses.
    """
    err = pre_stx.multisig.validate()
    if err:
        return err
    addr = pre_stx.multisig.address()
    if not encoding.encode_address(pre_stx.transaction.sender) == addr:
        raise error.BadTxnSenderError
    index = -1
    public_key = base64.b64decode(bytes(private_key, "ascii"))[32:]
    for s in range(len(pre_stx.multisig.subsigs)):
        if pre_stx.multisig.subsigs[s].public_key == public_key:
            index = s
            break
    if index == -1:
        raise error.InvalidSecretKeyError
    sig = raw_sign_transaction(pre_stx.transaction, private_key)
    pre_stx.multisig.subsigs[index].signature = sig
    return pre_stx


def merge_multisig_transactions(part_stxs):
    """
    Merge partially signed multisig transactions.

    Args:
        part_stxs (SignedTransaction[]): list of partially signed transactions

    Returns:
        (SignedTransaction, str): signed transaction with multisig containing
            signatures, transaction ID

    Note:
        Only use this if you are given two partially signed multisig
        transactions. To append a signature to a multisig transaction, just
        use sign_multisig_transaction()
    """

    if len(part_stxs) < 2:
        return "tried to merge less than two multisig transactions"

    ref_addr = None
    ref_txn = None
    for stx in part_stxs:
        if not ref_addr:
            ref_addr = stx.multisig.address()
            ref_txn = stx.transaction
        elif not stx.multisig.address() == ref_addr:
            raise error.MergeKeysMismatchError
    msigstx = None
    for stx in part_stxs:
        if not msigstx:
            msigstx = stx
        else:
            for s in range(len(stx.multisig.subsigs)):
                if stx.multisig.subsigs[s].signature:
                    if not msigstx.multisig.subsigs[s].signature:
                        msigstx.multisig.subsigs[s].signature = \
                            stx.multisig.subsigs[s].signature
                    elif not msigstx.multisig.subsigs[s].signature == \
                            stx.multisig.subsigs[s].signature:
                        raise error.DuplicateSigMismatchError
    txid = get_txid(ref_txn)
    return msigstx, txid


def sign_bid(bid, private_key):
    """
    Sign a bid.

    Args:
        bid (Bid): bid to be signed
        private_key (str): private_key of the bidder

    Returns:
        SignedBid: signed bid with the signature
    """
    temp = encoding.msgpack_encode(bid)
    to_sign = constants.bid_prefix + base64.b64decode(bytes(temp, "ascii"))
    private_key = base64.b64decode(bytes(private_key, "ascii"))
    signing_key = SigningKey(private_key[:32])
    signed = signing_key.sign(to_sign)
    sig = signed.signature
    signed = auction.SignedBid(bid, base64.b64encode(sig))
    return signed


def get_txid(txn):
    """
    Get a transaction's ID.

    Args:
        txn (Transaction): transaction to compute the ID of

    Returns:
        str: transaction ID
    """
    txn = encoding.msgpack_encode(txn)
    to_sign = constants.txid_prefix + base64.b64decode(bytes(txn, "ascii"))
    txidbytes = hashes.Hash(hashes.SHA512_256(), default_backend())
    txidbytes.update(to_sign)
    txid = txidbytes.finalize()
    txid = base64.b32encode(txid).decode()
    return encoding.undo_padding(txid)


def generate_account():
    """
    Generate an account.

    Returns:
        (str, str): private key, account address
    """
    sk = SigningKey.generate()
    vk = sk.verify_key
    a = encoding.encode_address(vk.encode())
    private_key = base64.b64encode(sk.encode() + vk.encode()).decode()
    return private_key, encoding.undo_padding(a)


def address_from_private_key(private_key):
    """
    Return the address for the private key.

    Args:
        private_key (str): private key of the account

    Returns:
        str: address of the account
    """
    pk = base64.b64decode(private_key)[32:]
    address = encoding.encode_address(pk)
    return address


def estimate_size(txn):
    sk, address = generate_account()
    stx, txid, sig = sign_transaction(txn, sk)
    return len(base64.b64decode(encoding.msgpack_encode(stx)))
