"""
Contains useful constants.
"""
KMD_AUTH_HEADER = "X-KMD-API-Token"
kmd_auth_header = KMD_AUTH_HEADER 
"""str: header key for kmd requests"""
ALGOD_AUTH_HEADER = "X-Algo-API-Token"
algod_auth_header = ALGOD_AUTH_HEADER 
"""str: header key for algod requests"""
INDEXER_AUTH_HEADER = "X-Indexer-API-Token"
indexer_auth_header = INDEXER_AUTH_HEADER 
"""str: header key for indexer requests"""
UNVERSIONED_PATHS = ["/health", "/versions", "/metrics", "/genesis"]
unversioned_paths = UNVERSIONED_PATHS 
"""str[]: paths that don't use the version path prefix"""
NO_AUTH = []
no_auth = NO_AUTH 
"""str[]: requests that don't require authentication"""


# transaction types
PAYMENT_TXN = "pay"
payment_txn = PAYMENT_TXN 
"""str: indicates a payment transaction"""
KEYREG_TXN = "keyreg"
keyreg_txn = KEYREG_TXN 
"""str: indicates a key registration transaction"""
ASSETCONFIG_TXN = "acfg"
assetconfig_txn = ASSETCONFIG_TXN 
"""str: indicates an asset configuration transaction"""
ASSETFREEZE_TXN = "afrz"
assetfreeze_txn = ASSETFREEZE_TXN 
"""str: indicates an asset freeze transaction"""
ASSETTRANSFER_TXN = "axfer"
assettransfer_txn = ASSETTRANSFER_TXN 
"""str: indicates an asset transfer transaction"""
APPCALL_TXN = "appl"
appcall_txn = APPCALL_TXN 
"""str: indicates an app call transaction, allows creating, deleting, and interacting with an application"""

# note field types
NOTE_FIELD_TYPE_DEPOSIT = "d"
note_field_type_deposit = NOTE_FIELD_TYPE_DEPOSIT
"""str: indicates a signed deposit in NoteField"""
NOTE_FIELD_TYPE_BID = "b"
note_field_type_bid = NOTE_FIELD_TYPE_BID
"""str: indicates a signed bid in NoteField"""
NOTE_FIELD_TYPE_SETTLEMENT = "s"
note_field_type_settlement = NOTE_FIELD_TYPE_SETTLEMENT
"""str: indicates a signed settlement in NoteField"""
NOTE_FIELD_TYPE_PARAMS = "p"
note_field_type_params = NOTE_FIELD_TYPE_PARAMS
"""str: indicates signed params in NoteField"""

# prefixes
TXID_PREFIX = b"TX"
txid_prefix = TXID_PREFIX
"""bytes: transaction prefix when signing"""
TGID_PREFIX = b"TG"
tgid_prefix = TGID_PREFIX
"""bytes: transaction group prefix when computing the group ID"""
BID_PREFIX = b"aB"
bid_prefix = BID_PREFIX
"""bytes: bid prefix when signing"""
BYTES_PREFIX = b"MX"
bytes_prefix = BYTES_PREFIX
"""bytes: bytes prefix when signing"""
MSIG_ADDR_PREFIX = "MultisigAddr"
msig_addr_prefix = MSIG_ADDR_PREFIX
"""str: prefix for multisig addresses"""
LOGIC_PREFIX = b"Program"
logic_prefix = LOGIC_PREFIX
"""bytes: program (logic) prefix when signing"""
LOGIC_DATA_PREFIX = b"ProgData"
logic_data_prefix = LOGIC_DATA_PREFIX
"""bytes: program (logic) data prefix when signing"""


HASH_LEN = 32
hash_len = HASH_LEN
"""int: how long various hash-like fields should be"""
CHECK_SUM_LEN_BYTES = 4
check_sum_len_bytes = CHECK_SUM_LEN_BYTES
"""int: how long checksums should be"""
KEN_LEN_BYTES = 32
key_len_bytes = KEN_LEN_BYTES
"""int: how long addresses are in bytes"""
ADDRESS_LEN = 58
address_len = ADDRESS_LEN
"""int: how long addresses are in base32, including the checksum"""
MNEMONIC_LEN = 25
mnemonic_len = MNEMONIC_LEN
"""int: how long mnemonic phrases are"""
MIN_TXN_FEE = 1000
min_txn_fee = MIN_TXN_FEE
"""int: minimum transaction fee"""
MICROALGOS_TO_ALGOS_RATIO = 1000000
microalgos_to_algos_ratio = MICROALGOS_TO_ALGOS_RATIO
"""int: how many microalgos per algo"""
METADATA_LENGTH = 32
metadata_length = METADATA_LENGTH
"""int: length of asset metadata"""
NOTE_MAX_LENGTH = 1024
note_max_length = NOTE_MAX_LENGTH
"""int: maximum length of note field"""
LEASE_LENGTH = 32
lease_length = LEASE_LENGTH
"""int: byte length of leases"""
MULTISIG_ACCOUNT_LIMIT = 255
multisig_account_limit = MULTISIG_ACCOUNT_LIMIT
"""int: maximum number of addresses in a multisig account"""
TX_GROUP_LIMIT = 16
tx_group_limit = TX_GROUP_LIMIT
"""int: maximum number of transaction in a transaction group"""
MAX_ASSET_DECIMALS = 19
max_asset_decimals = MAX_ASSET_DECIMALS
"""int: maximum value for decimals in assets"""

# logic sig related
LOGIC_SIG_MAX_COST = 20000
logic_sig_max_cost = LOGIC_SIG_MAX_COST
"""int: max execution cost of a teal program"""
LOGIC_SIG_MAX_SIZE = 1000
logic_sig_max_size = LOGIC_SIG_MAX_SIZE
"""int: max size of a teal program and its arguments in bytes"""
