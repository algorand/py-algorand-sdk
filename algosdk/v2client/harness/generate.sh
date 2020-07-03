#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 path-to-oas2-spec.json"
  exit 1
fi

THIS_DIR="$( cd "$(dirname "$0")" || exit ; pwd -P )"
PARENT_DIR="$THIS_DIR/.."

# generation of the specific models does not work, so generate all remove exceed files and models
openapi-generator generate -g python \
  -i "$1" -o "$THIS_DIR/gen" -t "$THIS_DIR" \
  --skip-validate-spec \
  --global-property excludeTests=true --global-property generateSourceCodeOnly=true \
  --global-property models --global-property modelDocs=false --global-property modelTests=false \
  --global-property supportingFiles=__init__.py

rm -rf "$PARENT_DIR/models"
mv "$THIS_DIR/gen/openapi_client/models" "$PARENT_DIR"

rm -rf "$THIS_DIR/gen"
rm -rf "$PARENT_DIR"/models/inline_response* "$PARENT_DIR"/models/account_state_delta.py \
"$PARENT_DIR"/models/application_information.py "$PARENT_DIR"/models/asset_information.py \
"$PARENT_DIR"/models/dryrun_state.py "$PARENT_DIR"/models/dryrun_txn_result.py \
"$PARENT_DIR"/models/error_response.py "$PARENT_DIR"/models/eval* "$PARENT_DIR"/models/version*

perl -i -ne 'next if m,inline_response200|account_state_delta|application_information|asset_information,; print' "$PARENT_DIR/models/__init__.py"
perl -i -ne 'next if m,dryrun_state|dryrun_txn_result|error_response|eval*|version*,; print' "$PARENT_DIR/models/__init__.py"
perl -pi -e 's/openapi_client/algosdk.v2client/g' "$PARENT_DIR/models/__init__.py"
