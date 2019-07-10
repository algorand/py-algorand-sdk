from collections import OrderedDict
import base64
from . import encoding, constants
from nacl.signing import SigningKey


class Bid:
    """Represents a bid in an auction.

    Args:
        bidder (str): address of the bidder
        bid_currency (int): how much external currency is being spent
        max_price (int): the maximum price the bidder is willing to pay
        bid_id (int): bid ID
        auction_key (str): address of the auction
        auction_id (int): auction ID

    Attributes:
        bidder (bytes)
        bid_currency (int)
        max_price (int)
        bid_id (int)
        auction_key (bytes)
        auction_id (int)

    """
    def __init__(self, bidder, bid_currency, max_price, bid_id, auction_key,
                 auction_id):
        self.bidder = encoding.decode_address(bidder)
        self.bid_currency = bid_currency
        self.max_price = max_price
        self.bid_id = bid_id
        self.auction_key = encoding.decode_address(auction_key)
        self.auction_id = auction_id

    def _dictify(self):
        od = OrderedDict()
        od["aid"] = self.auction_id
        od["auc"] = self.auction_key
        od["bidder"] = self.bidder
        od["cur"] = self.bid_currency
        od["id"] = self.bid_id
        od["price"] = self.max_price
        return od

    def sign(self, private_key):
        """
        Sign a bid.

        Args:
            private_key (str): private_key of the bidder

        Returns:
            SignedBid: signed bid with the signature
        """
        temp = encoding.msgpack_encode(self)
        to_sign = constants.bid_prefix + base64.b64decode(bytes(temp, "ascii"))
        private_key = base64.b64decode(bytes(private_key, "ascii"))
        signing_key = SigningKey(private_key[:constants.address_len_bytes])
        signed = signing_key.sign(to_sign)
        sig = signed.signature
        signed = SignedBid(self, base64.b64encode(sig))
        return signed

    @staticmethod
    def _undictify(d):
        return Bid(encoding.encode_address(d["bidder"]), d["cur"], d["price"],
                   d["id"], encoding.encode_address(d["auc"]), d["aid"])


class SignedBid:
    """
    Represents a signed bid in an auction.

    Args:
        bid (Bid): bid that was signed
        signature (str): the signature of the bidder

    Attributes:
        bid (Bid)
        signature (str)
    """
    def __init__(self, bid, signature):
        self.bid = bid
        self.signature = base64.b64decode(signature)

    def _dictify(self):
        od = OrderedDict()
        od["bid"] = self.bid._dictify()
        od["sig"] = self.signature
        return od

    @staticmethod
    def _undictify(d):
        return SignedBid(Bid._undictify(d["bid"]), base64.b64encode(d["sig"]))


class NoteField:
    """
    Can be encoded and added to a transaction.

    Args:
        signed_bid (SignedBid): bid with signature of bidder
        note_field_type (str): the type of note; see constants for possible
            types

    Attributes:
        signed_bid (SignedBid)
        note_field_type (str)
    """
    def __init__(self, signed_bid, note_field_type):
        self.signed_bid = signed_bid
        self.note_field_type = note_field_type

    def _dictify(self):
        od = OrderedDict()
        od["b"] = self.signed_bid._dictify()
        od["t"] = self.note_field_type
        return od

    @staticmethod
    def _undictify(d):
        return NoteField(SignedBid._undictify(d["b"]), d["t"])
