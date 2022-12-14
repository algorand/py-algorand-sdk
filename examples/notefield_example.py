# Example: working with NoteField
# We can put things in the "note" field of a transaction; here's an example
# with an auction bid. Note that you can put any bytes you want in the "note"
# field; you don't have to use the NoteField object.

import base64

import tokens

from algosdk import account, auction, constants, encoding, transaction
from algosdk.v2client import algod

acl = algod.AlgodClient(tokens.algod_token, tokens.algod_address)

# generate an account
private_key, public_key = account.generate_account()

# get suggested parameters
sp = acl.suggested_params()

# Set other parameters
amount = 100000
note = "Some Text".encode()
_, receiver = account.generate_account()

# create the NoteField object
bid_currency = 100
max_price = 15
bid_id = 18862
auction_key = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
auction_id = 93559

bid = auction.Bid(
    public_key, bid_currency, max_price, bid_id, auction_key, auction_id
)
signed_bid = bid.sign(private_key)

notefield = auction.NoteField(signed_bid, constants.note_field_type_bid)

# create the transaction
txn = transaction.PaymentTxn(
    public_key,
    sp,
    receiver,
    amount,
    note=base64.b64decode(encoding.msgpack_encode(notefield)),
)

# encode the transaction
encoded_txn = encoding.msgpack_encode(txn)
print("Encoded transaction:", encoded_txn, "\n")

# if someone else were to want to access the notefield from an encoded
# transaction, they could just decode the transaction
decoded_txn = encoding.msgpack_decode(encoded_txn)
decoded_notefield = encoding.msgpack_decode(base64.b64encode(decoded_txn.note))
print(
    "Decoded notefield from encoded transaction:", decoded_notefield.dictify()
)
