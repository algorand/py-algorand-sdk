# change if version changes
apiVersionPathPrefix = "/v1"
kmdAuthHeader = "X-KMD-API-Token"
algodAuthHeader = "X-Algo-API-Token"
unversionedPaths = ["/health", "/versions", "/metrics"]
noAuth = ["/health"]


# note field types
note_field_type_deposit = "d"
note_field_type_bid = "b"
note_field_type_settlement = "s"
note_field_type_params = "p"


checkSumLenBytes = 4
msigAddrPrefix = "MultisigAddr"
handleRenewTime = 60
minTxnFee = 1000

txidPrefix = bytes("TX", "ascii")
bidPrefix = bytes("aB", "ascii")