import base64
from collections import OrderedDict
import encoding


class Transaction:
    def __init__(self, sender, fee, first, last, note, gen, gh):
        self.type = None
        self.sender = sender  # str
        self.fee = fee  # possibly min txn fee
        self.firstValidRound = first  # num
        self.lastValidRound = last  # num
        self.note = note  # bytearray
        self.genesisID = gen  # str
        self.genesisHash = gh  # str


class PaymentTxn(Transaction):
    """Represents a payment transaction.
    Parameters
    ----------
    sender: string

    fee: int

    first: int
        first round for which the transaction is valid
    last: int
        last round for which the transaction is valid
    note: byte[]

    gen: string
        genesisID
    gh: string
        genesishash
    receiver: string

    amt: int

    closeRemainderTo: string
        if nonempty, account will be closed and
        remaining algos will be sent to this address
    """
    def __init__(self,  sender, fee, first, last, note, gen, gh, receiver, amt, closeRemainderTo=None):
        Transaction.__init__(self,  sender, fee, first, last, note, gen, gh)
        self.receiver = receiver
        self.amt = amt
        self.closeRemainderTo = closeRemainderTo
        self.type = "pay"

    def dictify(self):
        "Returns serialized transaction."
        od = OrderedDict()
        od["amt"] = self.amt
        if self.closeRemainderTo:
            od["close"] = correct_padding(self.closeRemainderTo)
        od["fee"] = self.fee
        od["fv"] = self.firstValidRound
        od["gen"] = self.genesisID
        od["gh"] = base64.b64decode(self.genesisHash)
        od["lv"] = self.lastValidRound
        if self.note:
            od["note"] = self.note
        od["rcv"] = base64.b32decode(correct_padding(self.receiver))
        od["snd"] = base64.b32decode(correct_padding(self.sender))
        od["type"] = self.type

        return od


class KeyregTxn(Transaction):
    def __init__(self, sender, fee, first, last, note, gen, gh, votekey, selkey, votefst, votelst, votekd):
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
        od["gh"] = base64.b64decode(self.genesisHash)
        od["lv"] = self.lastValidRound
        if self.note:
            od["note"] = self.note
        od["selkey"] = self.selkey
        od["snd"] = base64.b32decode(correct_padding(self.sender))
        od["type"] = self.type
        od["votefst"] = self.votefst,
        od["votekd"] = self.votekd,
        od["votekey"] = self.votepk,
        od["votelst"] = self.votelst
        return od


class SignedTransaction:
    def __init__(self, transaction, signature=None, multisig=None):
        self.signature = signature
        self.transaction = transaction
        self.multisig = multisig

    def dictify(self):
        od = OrderedDict()
        od["msig"] = self.multisig
        od["sig"] = self.signature
        od["txn"] = self.transaction.dictify()
        return od


def correct_padding(value):
    return value[:-6] + "===="
