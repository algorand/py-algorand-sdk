"""
Contains useful constants.
"""

# change if version changes
apiVersionPathPrefix = "/v1"
"""str: current path prefix for requests"""
kmdAuthHeader = "X-KMD-API-Token"
"""str: header key for kmd requests"""
algodAuthHeader = "X-Algo-API-Token"
"""str: header key for algod requests"""
unversionedPaths = ["/health", "/versions", "/metrics"]
"""str[]: paths that don't use the version path prefix"""
noAuth = ["/health"]
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


checkSumLenBytes = 4
"""int: how long checksums should be"""
msigAddrPrefix = "MultisigAddr"
"""str: prefix for multisig addresses"""
handleRenewTime = 60
"""int: how long it takes for a wallet handle to expire"""
minTxnFee = 1000
"""int: minimum transaction fee"""


txidPrefix = bytes("TX", "ascii")
"""bytes: transaction prefix when signing"""
bidPrefix = bytes("aB", "ascii")
"""bytes: bid prefix when signing"""
