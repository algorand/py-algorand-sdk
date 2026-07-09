#!/bin/bash
# Refresh the vendored post-quantum test vectors.
#
# The signing and mnemonic vectors are generated and validated directly via
# go-algorand by the algokit-polytest data factory:
#   https://github.com/algorandfoundation/algokit-polytest/blob/pq/resources/data-factory/main.go
#
# The ed25519 point-check known-answer test (KAT) comes from falcon-signatures:
#   https://github.com/algorandfoundation/falcon-signatures/blob/main/algorand/testdata/README.md
#
# NOTE: upstream vectors currently use the pre-rename msgpack key "pq"; once they
# are regenerated against post-rename go-algorand (key "pqsig") the legacy-decode
# tests in test_pq.py will need updating. Always re-run `make pytest-unit` after.
set -euo pipefail
cd "$(dirname "$0")"

POLYTEST=https://raw.githubusercontent.com/algorandfoundation/algokit-polytest/pq/resources/data-factory/data
for f in pqPayment pqDelegatedPayment pqRekeyedPayment pqRekeyedDelegatedPayment pqMnemonic; do
    curl -fL -o "$f.json" "$POLYTEST/$f.json"
done

FALCON=https://raw.githubusercontent.com/algorandfoundation/falcon-signatures/main/algorand/testdata
curl -fL -o lsig_address_kat.json "$FALCON/lsig_address_kat.json"
