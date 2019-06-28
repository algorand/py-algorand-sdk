import base64
import msgpack
from collections import OrderedDict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from . import error
from . import encoding
from . import constants


class Transaction:
    """
    Superclass for PaymentTxn and KeyregTxn.
    """
    def __init__(self, sender, fee, first, last, note, gen, gh):
        self.sender = encoding.decodeAddress(sender)
        self.fee = fee
        self.firstValidRound = first
        self.lastValidRound = last
        self.note = note
        self.genesisID = gen
        self.genesisHash = base64.b64decode(gh)

    def getSender(self):
        """Return the base32 encoding of the sender."""
        return encoding.encodeAddress(self.sender)

    def getGenesisHash(self):
        """Return the base64 encodi ng of the genesis hash."""
        return base64.b64encode(self.genesisHash).decode()


class PaymentTxn(Transaction):
    """
    Represents a payment transaction.

    Args:
        sender (str): address of the sender
        fee (int): transaction fee
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesishash
        receiver (str): address of the receiver
        amt (int): amount in microAlgos to be sent
        closeRemainderTo (str, optional): if nonempty, account will be closed
            and remaining algos will be sent to this address
        note (bytes, optional): encoded NoteField object
        gen (str, optional): genesisID

    Attributes:
        sender (bytes)
        fee (int)
        first (int)
        last (int)
        gh (bytes)
        receiver (bytes)
        amt (int)
        closeRemainderTo (bytes)
        note (bytes)
        gen (str)
    """

    def __init__(self, sender, fee, first, last, gh, receiver, amt,
                 closeRemainderTo=None, note=None, gen=None):
        Transaction.__init__(self,  sender, fee, first, last, note, gen, gh)
        self.receiver = encoding.decodeAddress(receiver)
        self.amt = amt
        self.closeRemainderTo = encoding.decodeAddress(closeRemainderTo)
        self.type = "pay"

    def dictify(self):
        od = OrderedDict()
        od["amt"] = self.amt
        if self.closeRemainderTo:
            od["close"] = self.closeRemainderTo
        od["fee"] = self.fee
        od["fv"] = self.firstValidRound
        if self.genesisID:
            od["gen"] = self.genesisID
        od["gh"] = self.genesisHash
        od["lv"] = self.lastValidRound
        if self.note:
            od["note"] = self.note
        od["rcv"] = self.receiver
        od["snd"] = self.sender
        od["type"] = self.type

        return od

    @staticmethod
    def undictify(d):
        crt = None
        note = None
        gen = None
        if "close" in d:
            crt = encoding.encodeAddress(d["close"])
        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        tr = PaymentTxn(encoding.encodeAddress(d["snd"]), d["fee"], d["fv"],
                        d["lv"], base64.b64encode(d["gh"]),
                        encoding.encodeAddress(d["rcv"]),
                        d["amt"], crt, note, gen)
        return tr

    def getReceiver(self):
        """Return the base32 encoding of the receiver."""
        return encoding.encodeAddress(self.receiver)

    def getCloseRemainderTo(self):
        """Return the base32 encoding of closeRemainderTo."""
        if not self.closeRemainderTo:
            return self.closeRemainderTo
        return encoding.encodeAddress(self.closeRemainderTo)


class KeyregTxn(Transaction):
    """
    Represents a key registration transaction.

    Args:
        sender (str): address of sender
        fee (int): transaction fee
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesishash
        votekey (str): participation public key
        selkey (str): VRF public key
        votefst (int): first round to vote
        votelst (int): last round to vote
        votekd (int): vote key dilution
        note (bytes, optional): encoded NoteField object
        gen (str): genesisID

    Attributes:
        sender (bytes)
        fee (int)
        first (int)
        last (int)
        gh (bytes)
        votepk (bytes)
        selkey (bytes)
        votefst (int)
        votelst (int)
        votekd (int)
        note (bytes)
        gen (str)
    """

    def __init__(self, sender, fee, first, last, gh, votekey, selkey,
                 votefst, votelst, votekd, note=None, gen=None):
        Transaction.__init__(self, sender, fee, first, last, note, gen, gh)
        self.votepk = encoding.decodeAddress(votekey)
        self.selkey = encoding.decodeAddress(selkey)
        self.votefst = votefst
        self.votelst = votelst
        self.votekd = votekd
        self.type = "keyreg"

    def dictify(self):
        od = OrderedDict()
        od["fee"] = self.fee
        od["fv"] = self.firstValidRound
        if self.genesisID:
            od["gen"] = self.genesisID
        od["gh"] = self.genesisHash
        od["lv"] = self.lastValidRound
        if self.note:
            od["note"] = self.note
        od["selkey"] = self.selkey
        od["snd"] = self.sender
        od["type"] = self.type
        od["votefst"] = self.votefst
        od["votekd"] = self.votekd
        od["votekey"] = self.votepk
        od["votelst"] = self.votelst
        return od

    @staticmethod
    def undictify(d):
        note = None
        gen = None
        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        k = KeyregTxn(encoding.encodeAddress(d["snd"]), d["fee"], d["fv"],
                      d["lv"], base64.b64encode(d["gh"]),
                      encoding.encodeAddress(d["votekey"]),
                      encoding.encodeAddress(d["selkey"]), d["votefst"],
                      d["votelst"], d["votekd"], note, gen)
        return k

    def getVoteKey(self):
        """Return the base32 encoding of the vote key."""
        return encoding.encodeAddress(self.votepk)

    def getSelectionKey(self):
        """Return the base32 encoding of the selection key."""
        return encoding.encodeAddress(self.selkey)


class SignedTransaction:
    """
    Represents a signed transaction.

    Args:
        transaction (Transaction): transaction that was signed
        signature (str, optional): signature of a single address
        multisig (Multisig, optional): multisig account and signatures

    Attributes:
        transaction (Transaction)
        signature (str)
        multisig (Multisig)
    """
    def __init__(self, transaction, signature=None, multisig=None):
        self.signature = None
        if signature:
            self.signature = base64.b64decode(signature)
        self.transaction = transaction
        self.multisig = multisig

    def dictify(self):
        od = OrderedDict()
        if self.multisig:
            od["msig"] = self.multisig.dictify()
        if self.signature:
            od["sig"] = self.signature
        od["txn"] = self.transaction.dictify()
        return od

    @staticmethod
    def undictify(d):
        msig = None
        sig = None
        if "sig" in d:
            sig = base64.b64encode(d["sig"])
        if "msig" in d:
            msig = Multisig.undictify(d["msig"])
        txnType = d["txn"]["type"]
        if txnType.__eq__("pay"):
            txn = PaymentTxn.undictify(d["txn"])
        else:
            txn = KeyregTxn.undictify(d["txn"])
        stx = SignedTransaction(txn, sig, msig)
        return stx

    def getSignature(self):
        """Return the base64 encoding of the signature."""
        return base64.b64encode(self.signature).decode()


class Multisig:
    """
    Represents a multisig account and signatures.

    Args:
        version (int): currently, the version is 1
        threshold (int): how many signatures are necessary
        addresses (str[]): addresses in the multisig account

    Attributes:
        version (int)
        threshold (int)
        subsigs (MultisigSubsig[])
    """
    def __init__(self, version, threshold, addresses):
        self.version = version
        self.threshold = threshold
        self.subsigs = []
        for a in addresses:
            self.subsigs.append(MultisigSubsig(encoding.decodeAddress(a)))

    def validate(self):
        """Check if the multisig account is valid."""
        if not self.version == 1:
            raise error.UnknownMsigVersionError
        if (self.threshold <= 0 or len(self.subsigs) == 0 or
                self.threshold > len(self.subsigs)):
            raise error.InvalidThresholdError

    def address(self):
        """Return the multisig account address."""
        msigBytes = (bytes(constants.msigAddrPrefix, "ascii") +
                     bytes([self.version]) + bytes([self.threshold]))
        for s in self.subsigs:
            msigBytes += s.public_key
        hash = hashes.Hash(hashes.SHA512_256(), default_backend())
        hash.update(msigBytes)
        addr = hash.finalize()
        return encoding.encodeAddress(addr)

    def dictify(self):
        od = OrderedDict()
        od["subsig"] = [subsig.dictify() for subsig in self.subsigs]
        od["thr"] = self.threshold
        od["v"] = self.version
        return od

    def json_dictify(self):
        od = OrderedDict()
        od["subsig"] = [subsig.json_dictify() for subsig in self.subsigs]
        od["thr"] = self.threshold
        od["v"] = self.version
        return od

    @staticmethod
    def undictify(d):
        subsigs = [MultisigSubsig.undictify(s) for s in d["subsig"]]
        msig = Multisig(d["v"], d["thr"], [])
        msig.subsigs = subsigs
        return msig

    def getAccountFromSig(self):
        """Return a Multisig object without signatures."""
        msig = Multisig(self.version, self.threshold, self.getPublicKeys())
        for s in msig.subsigs:
            s.signature = None
        return msig

    def getPublicKeys(self):
        """Return the base32 encoded addresses for the multisig account."""
        pks = [encoding.encodeAddress(s.public_key) for s in self.subsigs]
        return pks


class MultisigSubsig:
    """
    Attributes:
        public_key (bytes)
        signature (bytes)
    """
    def __init__(self, public_key, signature=None):
        self.public_key = public_key
        self.signature = signature

    def dictify(self):
        od = OrderedDict()
        od["pk"] = self.public_key
        if self.signature:
            od["s"] = self.signature
        return od

    def json_dictify(self):
        od = OrderedDict()
        od["pk"] = base64.b64encode(self.public_key).decode()
        if self.signature:
            od["s"] = base64.b64encode(self.signature).decode()
        return od

    @staticmethod
    def undictify(d):
        sig = None
        if "s" in d:
            sig = d["s"]
        mss = MultisigSubsig(d["pk"], sig)
        return mss


def writeToFile(txns, path, overwrite=True):
    """
    Write signed or unsigned transactions to a file.

    Args:
        txns (Transaction[] or SignedTransaction[]): can be a mix of both
        path (str): file to write to
        overwrite (bool): whether or not to overwrite what's already in the
            file; if False, transactions will be appended to the file
    """

    f = None
    if overwrite:
        f = open(path, "wb")
    else:
        f = open(path, "ab")

    for txn in txns:
        if isinstance(txn, Transaction):
            enc = msgpack.packb({"txn": txn.dictify()}, use_bin_type=True)
            f.write(enc)
        elif isinstance(txn, SignedTransaction):
            enc = msgpack.packb(txn.dictify(), use_bin_type=True)
            f.write(enc)


def retrieveFromFile(path):
    """
    Retrieve signed or unsigned transactions from a file.

    Args:
        path (str): file to read from

    Returns
        Transaction[] or SignedTransaction[]: can be a mix of both
    """

    f = open(path, "rb")
    txns = []
    unp = msgpack.Unpacker(f, raw=False)
    for txn in unp:
        if "sig" in txn or "msig" in txn:
            txns.append(SignedTransaction.undictify(txn))
        elif txn["txn"]["type"].__eq__("pay"):
            txns.append(PaymentTxn.undictify(txn["txn"]))
        elif txn["txn"]["type"].__eq__("keyreg"):
            txns.append(KeyregTxn.undictify(txn["txn"]))
    return txns
