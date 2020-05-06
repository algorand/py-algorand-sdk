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

# Build SDK testing environment
docker build -t py-sdk-testing -f Dockerfile "$(pwd)"

# Start test harness environment
./test-harness/scripts/up.sh

sleep 5

# Launch SDK testing
docker run -it \
     --network host \
     py-sdk-testing:latest 
