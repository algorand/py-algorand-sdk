import base64
from collections import OrderedDict
import encoding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class Transaction:
    def __init__(self, sender, fee, first, last, note, gen, gh):
        self.sender = encoding.decodeAddress(sender)  # str, decode into bytes
        self.fee = fee  # possibly min txn fee
        self.firstValidRound = first  # num
        self.lastValidRound = last  # num
        self.note = note  # bytearray
        self.genesisID = gen  # str
        self.genesisHash = base64.b64decode(gh)  # str


class PaymentTxn(Transaction):
    """
    Parameters
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

    closeRemainderTo: string
        if nonempty, account will be closed and
        remaining algos will be sent to this address

    note: byte[]
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


class KeyregTxn(Transaction):
    """
    Parameters
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
    votekey: byte[32]

    selkey: byte[32]

    votefst: int

    votelst: int

    votekd: int

    note: byte[]
    """
    def __init__(self, sender, fee, first, last, gen, gh, votekey, selkey, votefst, votelst, votekd, note=None):
        Transaction.__init__(self, sender, fee, first, last, note, gen, gh)
        self.votepk = votekey
        self.selkey = selkey
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
        od["votefst"] = self.votefst,
        od["votekd"] = self.votekd,
        od["votekey"] = self.votepk,
        od["votelst"] = self.votelst
        return od
    
    @staticmethod
    def undictify(d):
        note = None
        if "note" in d:
            note = d["note"]
        k = KeyregTxn(encoding.encodeAddress(d["snd"]), d["fee"], d["fv"], d["lv"], d["gen"], base64.b64encode(d["gh"]), d["votekey"], d["selkey"], d["votefst"], d["votelst"], d["votekd"], note)
        return k


class SignedTransaction:
    """
    Parameters
    ----------
    transaction: Transaction object

    signature: bytes

    multisig: Multisig object
    """
    def __init__(self, transaction, signature=None, multisig=None):
        self.signature = signature
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
            sig = d["sig"]
        if "msig" in d:
            msig = Multisig.undictify(d["msig"])
        txnType = d["txn"]["type"]
        if txnType.__eq__("pay"):
            txn = PaymentTxn.undictify(d["txn"])
        else:
            txn = KeyregTxn.undictify(d["txn"])
        stx = SignedTransaction(txn, sig, msig)
        return stx

msigAddrPrefix = "MultisigAddr"

class Multisig:
    """
    Parameters
    ----------
    version: int
        is currently always 1

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
            return "multisig unknown version"
        if self.threshold <= 0 or len(self.subsigs) == 0 or self.threshold > len(self.subsigs):
            return "invalid threshold"

    def address(self):
        msigBytes = bytes(msigAddrPrefix, "ascii") + bytes([self.version]) + bytes([self.threshold])
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
        msig = Multisig(self.version, self.threshold, self.subsigs[:])
        for s in msig.subsigs:
            s.signature = None
        return msig

    def getPublicKeys(self):
        pks = []
        for s in self.subsigs:
            pks.append(base64.b64encode(s.public_key).decode())
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
