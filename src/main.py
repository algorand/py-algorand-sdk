import base64
import transaction
import encoding
import kmd
import crypto
import algod
from collections import OrderedDict
import auction
import time
kmdToken = "bb24002c179d5d7b1ddf0735b9cfd2cb2ed922517fcd74b511ee0d65fa6c277b"
kmdAddress = "http://localhost:63831"
c = kmd.kmdClient(kmdToken, kmdAddress)

algodToken = "f40453efac65244a2763b195862aef0bea3abe21216b676d73936d2b4cc95518"
algodAddress = "http://localhost:8080"
a = algod.AlgodClient(algodToken, algodAddress)

ac1 = "DAXGIQRDRA7IUAHSNLX2A5DSC3MTN3C7Z46N2PDMBOPRUGPJ2AITQDZFNI"
ac2 = "D5KGQ6RXPUZZJXQNSKICXNV265UTPYLIFXJMDHR6FIEDQASGJLGXQPU3GQ"
ac3 = "MZ3CHNMITFDNEYWDGGCWT7JIVRCHN6J3T7IUTC7G7N7BZYZ7UUFJDSRF2I"
t = c.initWalletHandle("ab0d78030f74acaa153233b819029077", "")["wallet_handle_token"]
# print(t)
# print(c.generateKey(t, False))



prk = c.exportKey(t, "", ac1)["private_key"]

b = auction.Bid(ac1, 1000, 1.2, "helloworld", ac2, "helloworld,again")
notef = auction.NoteField(crypto.signBid(b, prk), "b")

note = encoding.msgpack_encode(notef)
print(note)
note = base64.b64decode(note)
# tr = transaction.KeyregTxn(ac1, 1000, 237170, 237180, 'testnet-v1.0', "Tf/p34jT1y27ooJPDP017DFHzCu3Vf/8QdcJKDoTbvY=", ac2, ac2, 237170, 237180, 123)


# print(encoding.msgpack_encode(tr))
tr = transaction.PaymentTxn(ac1, 1000, 304, 1004, 'network-v38', "Tf/p34jT1y27ooJPDP017DFHzCu3Vf/8QdcJKDoTbvY=", ac2, 200000, note=note)

stxbytes, txid, sig = crypto.signTransaction(tr, prk)
print(stxbytes)
print("sending transaction")
trxId = a.sendRawTransaction(stxbytes)
print(trxId)
print(txid)


time.sleep(10)



# print(a.suggestedParams())
print(a.pendingTransactions(0))
print("trx info")
# print(a.transactionInfo(ac1, "MO3MYPH436NJEB3VIYOHLPRDJDYV2POPQM4CS5A2POBOJ2JULZQA"))
print(a.transactionsByAddress(ac1, 1, 999, 0))
# transactionByID("I3RFLLO6ULXLHCFRQIGGEUKRSYPAKD4EWCBYOONVZLMPB4NBD5ZA"))
#duck aerobic light van chronic program merge mention brain fire deny duty steel minimum water race connect approve budget eight decorate viable enlist abstract pulse
