#!/usr/bin/env bash

set -euo pipefail

START=$(date "+%s")

THIS=$(basename "$0")
ENV_FILE=".test-env"

set -a
source "$ENV_FILE"
set +a

rootdir=$(dirname "$0")
pushd "$rootdir"

## Reset test harness
if [ -d "$SDK_TESTING_HARNESS" ]; then
  pushd "$SDK_TESTING_HARNESS"
  ./scripts/down.sh
  popd
  rm -rf "$SDK_TESTING_HARNESS"
else
  echo "$THIS: directory $SDK_TESTING_HARNESS does not exist - NOOP"
fi

git clone --depth 1 --single-branch --branch "$SDK_TESTING_BRANCH" "$SDK_TESTING_URL" "$SDK_TESTING_HARNESS"


if [[ $OVERWRITE_TESTING_ENVIRONMENT == 1 ]]; then
  echo "$THIS: OVERWRITE replaced $SDK_TESTING_HARNESS/.env with $ENV_FILE:"
  cp "$ENV_FILE" "$SDK_TESTING_HARNESS"/.env
fi

## Copy feature files into the project resources
if [[ $REMOVE_LOCAL_FEATURES == 1 ]]; then
  echo "$THIS: OVERWRITE wipes clean tests/features"
  if [[ $VERBOSE_HARNESS == 1 ]]; then
    ( tree tests/features && echo "$THIS: see the previous for files deleted" ) || true
  fi
  rm -rf tests/features
fi
mkdir -p tests/features
cp -r "$SDK_TESTING_HARNESS"/features/* tests/features
if [[ $VERBOSE_HARNESS == 1 ]]; then
  ( tree tests/features && echo "$THIS: see the previous for files copied over" ) || true
fi
echo "$THIS: seconds it took to get to end of cloning and copying: $(($(date "+%s") - START))s"

## Start test harness environment
pushd "$SDK_TESTING_HARNESS"
./scripts/up.sh
popd
echo "$THIS: seconds it took to finish testing sdk's up.sh: $(($(date "+%s") - START))s"
echo ""
echo "--------------------------------------------------------------------------------"
echo "|"
echo "|    To run sandbox commands, cd into $SDK_TESTING_HARNESS/.sandbox             "
echo "|"
echo "--------------------------------------------------------------------------------"
