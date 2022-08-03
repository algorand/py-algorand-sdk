#!/usr/bin/env bash

START=$(date "+%s")

set -e

rootdir=`dirname $0`
pushd $rootdir

# Reset test harness
rm -rf test-harness
git clone --single-branch --branch trim-indexer https://github.com/algorand/algorand-sdk-testing.git test-harness

## Copy feature files into the project resources
mkdir -p tests/features
cp -r test-harness/features/* tests/features
echo "time till end of cloning + copying: " + $(($(date "+%s") - $START))


# Build SDK testing environment
docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" -f Dockerfile "$(pwd)"
echo "time till end of building PYSDK: " + $(($(date "+%s") - $START))


# Start test harness environment
./test-harness/scripts/up.sh
echo "time till end of up.sh: " + $(($(date "+%s") - $START))

while [ $(curl -sL -w "%{http_code}\\n" "http://localhost:60002/v2/accounts" -o /dev/null --connect-timeout 3 --max-time 5) -ne "200" ]
do
  sleep 1
done
echo "time till indexer-live is ready: " + $(($(date "+%s") - $START))

# Launch SDK testing
docker run -it \
     --network host \
     py-sdk-testing:latest 
echo "time till end of all tests: " + $(($(date "+%s") - $START))

