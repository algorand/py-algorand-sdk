#!/usr/bin/env bash
set -e

# Move to project root, relative to script location
rootdir=`dirname $0`
pushd "${rootdir}/../../.."

rm -rf temp
rm -rf test/cucumber/features
git clone --single-branch --branch develop https://github.com/algorand/algorand-sdk-testing.git temp

mv temp/features test/cucumber/features

docker build -t py-sdk-testing -f test/cucumber/docker/Dockerfile "$(pwd)"

# Start test harness environment
./temp/scripts/up.sh

# Build and launch SDK testing container
docker run -it \
     --network host \
     py-sdk-testing:latest 
