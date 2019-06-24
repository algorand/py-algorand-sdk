from collections import OrderedDict
import base64
from . import encoding

class Bid:
    def __init__(self, bidder, bid_currency, max_price, bid_id, auction_key, auction_id):
        self.bidder = encoding.decodeAddress(bidder)
        self.bid_currency = bid_currency # how much external currency
        self.max_price = max_price
        self.bid_id = bid_id
        self.auction_key = encoding.decodeAddress(auction_key)
        self.auction_id = auction_id
    
    def dictify(self):
        od = OrderedDict()
        od["aid"] = self.auction_id
        od["auc"] = self.auction_key
        od["bidder"] = self.bidder
        od["cur"] = self.bid_currency
        od["id"] = self.bid_id
        od["price"] = self.max_price
        return od
    
    @staticmethod
    def undictify(d):
        return Bid(encoding.encodeAddress(d["bidder"]), d["cur"], d["price"], d["id"], encoding.encodeAddress(d["auc"]), d["aid"])

class SignedBid:
    def __init__(self, bid, signature):
        self.bid = bid
        self.signature = base64.b64decode(signature)
    
    def dictify(self):
        od = OrderedDict()
        od["bid"] = self.bid.dictify()
        od["sig"] = self.signature
        return od
    
    @staticmethod
    def undictify(d):
        return SignedBid(Bid.undictify(d["bid"]), base64.b64encode(d["sig"]))


class NoteField:
    def __init__(self, signed_bid, note_field_type):
        self.signed_bid = signed_bid
        self.note_field_type = note_field_type

    def dictify(self):
        od = OrderedDict()
        od["b"] = self.signed_bid.dictify()
        od["t"] = self.note_field_type
        return od

    @staticmethod
    def undictify(d):
        return NoteField(SignedBid.undictify(d["b"]), d["t"])


    
    


