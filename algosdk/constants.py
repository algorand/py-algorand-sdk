from typing import List

"""
Contains useful constants.
"""
KMD_AUTH_HEADER = "X-KMD-API-Token"
"""str: header key for kmd requests"""
ALGOD_AUTH_HEADER = "X-Algo-API-Token"
"""str: header key for algod requests"""
INDEXER_AUTH_HEADER = "X-Indexer-API-Token"
"""str: header key for indexer requests"""
UNVERSIONED_PATHS = ["/health", "/versions", "/metrics", "/genesis", "/ready"]
"""str[]: paths that don't use the version path prefix"""
NO_AUTH: List[str] = []
"""str[]: requests that don't require authentication"""


# transaction types
PAYMENT_TXN = "pay"
"""str: indicates a payment transaction"""
KEYREG_TXN = "keyreg"
"""str: indicates a key registration transaction"""
ASSETCONFIG_TXN = "acfg"
"""str: indicates an asset configuration transaction"""
ASSETFREEZE_TXN = "afrz"
"""str: indicates an asset freeze transaction"""
ASSETTRANSFER_TXN = "axfer"
"""str: indicates an asset transfer transaction"""
APPCALL_TXN = "appl"
"""str: indicates an app call transaction, allows creating, deleting, and interacting with an application"""
STATEPROOF_TXN = "stpf"
"""str: indicates an state proof transaction"""

# note field types
NOTE_FIELD_TYPE_DEPOSIT = "d"
"""str: indicates a signed deposit in NoteField"""
NOTE_FIELD_TYPE_BID = "b"
"""str: indicates a signed bid in NoteField"""
NOTE_FIELD_TYPE_SETTLEMENT = "s"
"""str: indicates a signed settlement in NoteField"""
NOTE_FIELD_TYPE_PARAMS = "p"
"""str: indicates signed params in NoteField"""

# prefixes
TXID_PREFIX = b"TX"
"""bytes: transaction prefix when signing"""
TGID_PREFIX = b"TG"
"""bytes: transaction group prefix when computing the group ID"""
BID_PREFIX = b"aB"
"""bytes: bid prefix when signing"""
BYTES_PREFIX = b"MX"
"""bytes: bytes prefix when signing"""
MSIG_ADDR_PREFIX = "MultisigAddr"
"""str: prefix for multisig addresses"""
LOGIC_PREFIX = b"Program"
"""bytes: program (logic) prefix when signing"""
LOGIC_DATA_PREFIX = b"ProgData"
"""bytes: program (logic) data prefix when signing"""
APPID_PREFIX = b"appID"
"""bytes: application ID prefix when signing"""


HASH_LEN = 32
"""int: how long various hash-like fields should be"""
CHECK_SUM_LEN_BYTES = 4
"""int: how long checksums should be"""
KEN_LEN_BYTES = 32
"""int: how long addresses are in bytes"""
ADDRESS_LEN = 58
"""int: how long addresses are in base32, including the checksum"""
MNEMONIC_LEN = 25
"""int: how long mnemonic phrases are"""
MIN_TXN_FEE = 1000
"""int: minimum transaction fee"""
MICROALGOS_TO_ALGOS_RATIO = 1000000
"""int: how many microalgos per algo"""
METADATA_LENGTH = 32
"""int: length of asset metadata"""
NOTE_MAX_LENGTH = 1024
"""int: maximum length of note field"""
LEASE_LENGTH = 32
"""int: byte length of leases"""
MULTISIG_ACCOUNT_LIMIT = 255
"""int: maximum number of addresses in a multisig account"""
TX_GROUP_LIMIT = 16
"""int: maximum number of transaction in a transaction group"""
MAX_ASSET_DECIMALS = 19
"""int: maximum value for decimals in assets"""

# logic sig related
LOGIC_SIG_MAX_COST = 20000
"""int: max execution cost of a teal program"""
LOGIC_SIG_MAX_SIZE = 1000
"""int: max size of a teal program and its arguments in bytes"""

APP_PAGE_MAX_SIZE = 2048
"""int: max size of a page for an application in bytes"""

ZERO_ADDRESS = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
"""str: algorand encoded address of 32 zero bytes"""

# for backward compatibility:
kmd_auth_header = KMD_AUTH_HEADER
algod_auth_header = ALGOD_AUTH_HEADER
indexer_auth_header = INDEXER_AUTH_HEADER
unversioned_paths = UNVERSIONED_PATHS
no_auth = NO_AUTH
payment_txn = PAYMENT_TXN
keyreg_txn = KEYREG_TXN
assetconfig_txn = ASSETCONFIG_TXN
assetfreeze_txn = ASSETFREEZE_TXN
assettransfer_txn = ASSETTRANSFER_TXN
appcall_txn = APPCALL_TXN
note_field_type_deposit = NOTE_FIELD_TYPE_DEPOSIT
note_field_type_bid = NOTE_FIELD_TYPE_BID
note_field_type_settlement = NOTE_FIELD_TYPE_SETTLEMENT
note_field_type_params = NOTE_FIELD_TYPE_PARAMS
txid_prefix = TXID_PREFIX
tgid_prefix = TGID_PREFIX
bid_prefix = BID_PREFIX
bytes_prefix = BYTES_PREFIX
msig_addr_prefix = MSIG_ADDR_PREFIX
logic_prefix = LOGIC_PREFIX
logic_data_prefix = LOGIC_DATA_PREFIX
hash_len = HASH_LEN
check_sum_len_bytes = CHECK_SUM_LEN_BYTES
key_len_bytes = KEN_LEN_BYTES
address_len = ADDRESS_LEN
mnemonic_len = MNEMONIC_LEN
min_txn_fee = MIN_TXN_FEE
microalgos_to_algos_ratio = MICROALGOS_TO_ALGOS_RATIO
metadata_length = METADATA_LENGTH
note_max_length = NOTE_MAX_LENGTH
lease_length = LEASE_LENGTH
multisig_account_limit = MULTISIG_ACCOUNT_LIMIT
tx_group_limit = TX_GROUP_LIMIT
max_asset_decimals = MAX_ASSET_DECIMALS
logic_sig_max_cost = LOGIC_SIG_MAX_COST
logic_sig_max_size = LOGIC_SIG_MAX_SIZE
app_page_max_size = APP_PAGE_MAX_SIZE
stateproof_txn = STATEPROOF_TXN
