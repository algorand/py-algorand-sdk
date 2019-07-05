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


# note field types
note_field_type_deposit = "d"
"""str: indicates a signed deposit in NoteField"""
note_field_type_bid = "b"
"""str: indicates a signed bid in NoteField"""
note_field_type_settlement = "s"
"""str: indicates a signed settlement in NoteField"""
note_field_type_params = "p"
"""str: indicates signed params in NoteField"""


check_sum_len_bytes = 4
"""int: how long checksums should be"""
msig_addr_prefix = "MultisigAddr"
"""str: prefix for multisig addresses"""
handle_renew_time = 60
"""int: how long it takes for a wallet handle to expire"""
min_txn_fee = 1000
"""int: minimum transaction fee"""


txid_prefix = bytes("TX", "ascii")
"""bytes: transaction prefix when signing"""
bid_prefix = bytes("aB", "ascii")
"""bytes: bid prefix when signing"""
