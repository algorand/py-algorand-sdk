#!/usr/bin/env bash

set -e

rootdir=`dirname $0`
pushd $rootdir

# Reset test harness
rm -rf test-harness
git clone --single-branch --branch ${TESTING_BRANCH} ${TESTING_URL} test-harness

## Copy feature files into the project resources
mkdir -p tests/features
cp -r test-harness/features/* tests/features

echo "DOCKERIZE_PYSDK-->${DOCKERIZE_PYSDK}"
if [[ ${DOCKERIZE_PYSDK}==true ]]; then
  echo "Building SDK docker for a full integration to run after algod and indexer docker builds"
  docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" -f Dockerfile "$(pwd)"
fi


UP_ENV=${LOCAL_TESTENV:-$(pwd)/test-harness/.up-env}
echo "UP_ENV-->${UP_ENV}"

# Start test harness environment
./test-harness/scripts/up.sh -f ${UP_ENV}

while [ $(curl -sL -w "%{http_code}\\n" "http://localhost:59999/v2/accounts" -o /dev/null --connect-timeout 3 --max-time 5) -ne "200" ]
do
  sleep 1
done

echo "algod is ready for testing"

if [[ ${DOCKERIZE_PYSDK}==true ]]; then
  echo "Launching SDK testing via the SDK docker image"
  docker run -it --network host py-sdk-testing:latest
fi

