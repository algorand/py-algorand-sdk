#!/usr/bin/env bash

set -e

rootdir=`dirname $0`
pushd $rootdir

# Reset test harness
rm -rf test-harness
git clone --single-branch --branch develop https://github.com/algorand/algorand-sdk-testing.git test-harness

## Copy feature files into the project resources
mkdir -p test/features
cp -r test-harness/features/* test/features

# Start test harness environment
./test-harness/scripts/up.sh

# dependencies
pip3 install behave
behave test -f progress2

# Stop test harness environment
./test-harness/scripts/down.sh