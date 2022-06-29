#!/usr/bin/env bash

set -e

rootdir=`dirname $0`
pushd $rootdir

# Reset test harness
rm -rf test-harness
# TODO: Before merging, change branch back to master
git clone --single-branch --branch box-path-tests https://github.com/algorand/algorand-sdk-testing.git test-harness

## Copy feature files into the project resources
mkdir -p tests/features
cp -r test-harness/features/* tests/features

# Build SDK testing environment
docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" -f Dockerfile "$(pwd)"

# Start test harness environment
./test-harness/scripts/up.sh

while [ $(curl -sL -w "%{http_code}\\n" "http://localhost:59999/v2/accounts" -o /dev/null --connect-timeout 3 --max-time 5) -ne "200" ]
do
  sleep 1
done

# Launch SDK testing
docker run -it \
     --network host \
     py-sdk-testing:latest 
