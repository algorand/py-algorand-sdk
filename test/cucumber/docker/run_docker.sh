#!/usr/bin/env bash
set -e

# Move to project root, relative to script location
rootdir=`dirname $0`
pushd "${rootdir}/../../.."

rm -rf temp
rm -rf test/cucumber/features
git clone --single-branch --branch develop https://github.com/algorand/algorand-sdk-testing.git temp

# Disable unimplemented tests
rm temp/features/integration/indexer.feature
rm temp/features/unit/v2*feature

# Copy feature files into project
mv temp/features test/cucumber/features

# Start test harness environment
./temp/scripts/up.sh

# Build and launch SDK testing container
docker build -t py-sdk-testing -f test/cucumber/docker/Dockerfile "$(pwd)"
docker run -it \
     --network host \
     py-sdk-testing:latest 
