from algosdk import transaction
from utils import get_algod_client

algod_client = get_algod_client()

# example: TRANSACTION_KEYREG_ONLINE_CREATE
# get suggested parameters
params = algod_client.suggested_params()

votekey = "eXq34wzh2UIxCZaI1leALKyAvSz/+XOe0wqdHagM+bw="
selkey = "X84ReKTmp+yfgmMCbbokVqeFFFrKQeFZKEXG89SXwm4="

num_rounds = int(1e5)  # sets up keys for 100000 rounds
key_dilution = int(num_rounds**0.5)  # dilution default is sqrt num rounds

# create transaction
online_keyreg = transaction.KeyregTxn(
    sender="EW64GC6F24M7NDSC5R3ES4YUVE3ZXXNMARJHDCCCLIHZU6TBEOC7XRSBG4",
    votekey=votekey,
    selkey=selkey,
    votefst=params.first,
    votelst=params.first + num_rounds,
    votekd=key_dilution,
    sp=params,
)
print(online_keyreg.dictify())
# example: TRANSACTION_KEYREG_ONLINE_CREATE

# example: TRANSACTION_KEYREG_OFFLINE_CREATE
# get suggested parameters
params = algod_client.suggested_params()

# create keyreg transaction to take this account offline
offline_keyreg = transaction.KeyregTxn(
    sender="EW64GC6F24M7NDSC5R3ES4YUVE3ZXXNMARJHDCCCLIHZU6TBEOC7XRSBG4",
    sp=params,
    votekey=None,
    selkey=None,
    votefst=None,
    votelst=None,
    votekd=None,
)
print(offline_keyreg.dictify())
# example: TRANSACTION_KEYREG_OFFLINE_CREATE
