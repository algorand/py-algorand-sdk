#!/usr/bin/env bash

START=$(date "+%s")

set -e

ENV_FILE=".test-env"
source $ENV_FILE

rootdir=$(dirname "$0")
pushd "$rootdir"

## Reset test harness
rm -rf "$SDK_TESTING_HARNESS"
git clone --single-branch --branch "$SDK_TESTING_BRANCH" "$SDK_TESTING_URL" "$SDK_TESTING_HARNESS"

## OVERWRITE incoming .env with .test-env
cp "$ENV_FILE" "$SDK_TESTING_HARNESS"/.env

## Copy feature files into the project resources
mkdir -p tests/features
cp -r "$SDK_TESTING_HARNESS"/features/* tests/features
echo "run_integration.sh: seconds it took to get to end of cloning + copying: " + $(($(date "+%s") - $START))


## Start test harness environment
pushd "$SDK_TESTING_HARNESS"
./scripts/up.sh
popd
echo "run_integration.sh: seconds it took to finish testing sdk's up.sh: " + $(($(date "+%s") - $START))
echo "To run sandbox commands, cd into $SDK_TESTING_HARNESS/$SANDBOX"
echo "time till end of test-harness bootstrapping: " + $(($(date "+%s") - $START))

