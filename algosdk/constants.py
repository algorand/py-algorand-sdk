"""
Contains useful constants.
"""

# change if version changes
api_version_path_prefix = "/v1"
"""str: current path prefix for requests"""
kmd_auth_header = "X-KMD-API-Token"
"""str: header key for kmd requests"""
algod_auth_header = "X-Algo-API-Token"
"""str: header key for algod requests"""
unversioned_paths = ["/health", "/versions", "/metrics"]
"""str[]: paths that don't use the version path prefix"""
no_auth = ["/health"]
"""str[]: requests that don't require authentication"""


# transaction types
payment_txn = "pay"
"""str: indicates a payment transaction"""
keyreg_txn = "keyreg"
"""str: indicates a key registration transaction"""
assetconfig_txn = "acfg"
"""str: indicates an asset configuration transaction"""
assetfreeze_txn = "afrz"
"""str: indicates an asset freeze transaction"""


# note field types
note_field_type_deposit = "d"
"""str: indicates a signed deposit in NoteField"""
note_field_type_bid = "b"
"""str: indicates a signed bid in NoteField"""
note_field_type_settlement = "s"
"""str: indicates a signed settlement in NoteField"""
note_field_type_params = "p"
"""str: indicates signed params in NoteField"""


# prefixes
txid_prefix = b"TX"
"""bytes: transaction prefix when signing"""
tgid_prefix = b"TG"
"""bytes: transaction group prefix when computing the group ID"""
bid_prefix = b"aB"
"""bytes: bid prefix when signing"""
bytes_prefix = b"MX"
"""bytes: bytes prefix when signing"""
msig_addr_prefix = "MultisigAddr"
"""str: prefix for multisig addresses"""


check_sum_len_bytes = 4
"""int: how long checksums should be"""
signing_key_len_bytes = 32
"""int: how long addresses are in bytes"""
address_len = 58
"""int: how long addresses are in base32, including the checksum"""
mnemonic_len = 25
"""int: how long mnemonic phrases are"""
min_txn_fee = 1000
"""int: minimum transaction fee"""
microalgos_to_algos_ratio = 1000000
"""int: how many microalgos per algo"""
