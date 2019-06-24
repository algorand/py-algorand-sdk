import base64
import msgpack
from collections import OrderedDict
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from . import error
from . import encoding
from . import constants


class Transaction:
    def __init__(self, sender, fee, first, last, note, gen, gh):
        self.sender = encoding.decodeAddress(sender)  # str, decode into bytes
        self.fee = fee  # possibly min txn fee
        self.firstValidRound = first  # num
        self.lastValidRound = last  # num
        self.note = note  # bytearray
        self.genesisID = gen  # str
        self.genesisHash = base64.b64decode(gh)  # str

    def getSender(self):
        return encoding.encodeAddress(self.sender)

    def getGenesisHash(self):
        return base64.b64encode(self.genesisHash).decode()

class PaymentTxn(Transaction):
    """
    Attributes
    ----------
    sender: string

    fee: int

    first: int
        first round for which the transaction is valid
    last: int
        last round for which the transaction is valid

    gen: string
        genesisID
    gh: string
        genesishash
    receiver: string

    amt: int

    closeRemainderTo: string, optional
        if nonempty, account will be closed and
        remaining algos will be sent to this address

    note: byte[], optional
    """
    def __init__(self, sender, fee, first, last, gen, gh, receiver, amt, closeRemainderTo=None, note=None):
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
        if "close" in d:
            crt = encoding.encodeAddress(d["close"])
        if "note" in d:
            note = d["note"]
        tr = PaymentTxn(encoding.encodeAddress(d["snd"]), d["fee"], d["fv"], d["lv"], d["gen"], base64.b64encode(d["gh"]), encoding.encodeAddress(d["rcv"]), d["amt"], crt, note)
        return tr

    def getReceiver(self):
        return encoding.encodeAddress(self.receiver)
    
    def getCloseRemainderTo(self):
        if not self.closeRemainderTo:
            return self.closeRemainderTo
        return encoding.encodeAddress(self.closeRemainderTo)


class KeyregTxn(Transaction):
    """
    Attributes
    ----------
    sender: string

    fee: int

    first: int
        first round for which the transaction is valid
    last: int
        last round for which the transaction is valid

    gen: string
        genesisID
    gh: string
        genesishash
    votekey: string

    selkey: string

    votefst: int

    votelst: int

    votekd: int

    note: byte[], optional
    """
    def __init__(self, sender, fee, first, last, gen, gh, votekey, selkey, votefst, votelst, votekd, note=None):
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
        if "note" in d:
            note = d["note"]
        k = KeyregTxn(encoding.encodeAddress(d["snd"]), d["fee"], d["fv"], d["lv"], d["gen"], base64.b64encode(d["gh"]), encoding.encodeAddress(d["votekey"]), encoding.encodeAddress(d["selkey"]), d["votefst"], d["votelst"], d["votekd"], note)
        return k

    def getVotingKey(self):
        return encoding.encodeAddress(self.votepk)

    def getSelectionKey(self):
        return encoding.encodeAddress(self.selkey)


class SignedTransaction:
    """
    Parameters
    ----------
    transaction: Transaction

    signature: string

    multisig: Multisig
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
        return base64.b64encode(self.signature).decode()




class Multisig:
    """
    Parameters
    ----------
    version: int
        the version is currently 1

    threshold: int

    addresses: string[]
    """
    def __init__(self, version, threshold, addresses):
        self.version = version 
        self.threshold = threshold
        self.subsigs = []
        for a in addresses: 
            self.subsigs.append(MultisigSubsig(encoding.decodeAddress(a)))

    def validate(self):
        if not self.version == 1:
            raise error.UnknownMsigVersionError
        if self.threshold <= 0 or len(self.subsigs) == 0 or self.threshold > len(self.subsigs):
            raise error.InvalidThresholdError

    def address(self):
        msigBytes = bytes(constants.msigAddrPrefix, "ascii") + bytes([self.version]) + bytes([self.threshold])
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
        """Returns a Multisig object without signatures."""
        msig = Multisig(self.version, self.threshold, self.subsigs[:])
        for s in msig.subsigs:
            s.signature = None
        return msig

    def getPublicKeys(self):
        """Returns the base64 encoded addresses for the multisig account."""
        pks = [encoding.encodeAddress(s.public_key) for s in self.subsigs]
        return pks

class MultisigSubsig:
    def __init__(self, public_key, signature = None):
        self.public_key = public_key # bytes
        self.signature = signature # bytes

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
    Writes signed or unsigned transactions to a file.

    Parameters
    ----------
    txns: list of Transactions or SignedTransactions

    path: string
        file to write to

    overwrite: boolean
        whether or not to overwrite what's already in the file
        if False, transactions will be appended to the file
    """

    f = None
    if overwrite:
        f = open(path, "wb")
    else:
        f = open(path, "ab")

    for txn in txns:
        if isinstance(txn, Transaction):
            enc = msgpack.packb({"txn": txn.dictify()}, use_bin_type=True)
            print(base64.b64encode(enc))
            f.write(enc)
        elif isinstance(txn, SignedTransaction):
            enc = msgpack.packb(txn.dictify(), use_bin_type = True)
            print(base64.b64encode(enc))
            f.write(enc)


def retrieveFromFile(path):
    """
    Retrieves signed or unsigned transactions from a file.

    Parameters
    ----------
    path: string
        file to read from

    Returns
    -------
    list of Transactions or SignedTransactions
    """

    f = open(path, "rb")
    txns = []
    unp = msgpack.Unpacker(f, raw=False)
    for txn in unp:
        if "sig" in txn:
            txns.append(SignedTransaction.undictify(txn))
        elif txn["txn"]["type"].__eq__("pay"):
            txns.append(PaymentTxn.undictify(txn["txn"]))
        elif txn["txn"]["type"].__eq__("keyreg"):
            txns.append(KeyregTxn.undictify(txn["txn"]))
    return txns