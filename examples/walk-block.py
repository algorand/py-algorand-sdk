import algosdk.transaction as txn
import algosdk.encoding as enc
from utils import algod_env, get_algod_client

algod = get_algod_client(*algod_env())
latest = algod.status().get("last-round")

# Take an existing SDK return value, and turn it into a nice object
bi = algod.block_info(latest, "msgpack")
block = enc.undictify(enc.algo_msgp_decode(bi))
# walk the payset
for txn in block.block.payset:
    print(txn.stxn.transaction.sender)


# Or we can add new calls that coerce the msgp before giving it out
for txn in algod.block(latest - 1).block.payset:
    print(txn.stxn.transaction.sender)
