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
# The factory builds against a go-algorand git submodule, so the vectors
# reflect whichever commit that submodule is pinned to. Check the pin to know
# which protocol behaviour a refresh brings in:
#   https://github.com/algorandfoundation/algokit-polytest/tree/pq/resources/data-factory
#
# Always re-run `make pytest-unit` after refreshing: a change to the wire key
# or to the post-quantum signing payload surfaces as a failure there.
set -euo pipefail
cd "$(dirname "$0")"

POLYTEST=https://raw.githubusercontent.com/algorandfoundation/algokit-polytest/pq/resources/data-factory/data
for f in pqPayment pqDelegatedPayment pqRekeyedPayment pqRekeyedDelegatedPayment pqMnemonic; do
    curl -fL -o "$f.json" "$POLYTEST/$f.json"
done

FALCON=https://raw.githubusercontent.com/algorandfoundation/falcon-signatures/main/algorand/testdata
curl -fL -o lsig_address_kat.json "$FALCON/lsig_address_kat.json"
