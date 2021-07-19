"""
Contains useful constants.
"""

KMD_AUTH_HEADER = "X-KMD-API-Token"
"""str: header key for kmd requests"""
ALGOD_AUTH_HEADER = "X-Algo-API-Token"
"""str: header key for algod requests"""
INDEXER_AUTH_HEADER = "X-Indexer-API-Token"
"""str: header key for indexer requests"""
UNVERSIONED_PATHS = ["/health", "/versions", "/metrics", "/genesis"]
"""str[]: paths that don't use the version path prefix"""
NO_AUTH = []
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


HASH_LEN = 32
"""int: how long various hash-like fields should be"""
CHECK_SUM_LEN_BYTES = 4
"""int: how long checksums should be"""
KEY_LEN_BYTES = 32
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
