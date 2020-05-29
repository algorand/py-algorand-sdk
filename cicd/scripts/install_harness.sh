#!/bin/bash

mkdir -p dist

if [ -z ${ALGORAND_SDK_TESTING_HARNESS_PATH} ]; then
    curl -o dist/algorand-sdk-testing-latest.tar.gz https://algorand-sdk-testing.s3.amazonaws.com/dist/algorand-sdk-testing-latest.tar.gz
else
    cp ${ALGORAND_SDK_TESTING_HARNESS_PATH} dist
fi

tar xf dist/algorand-sdk-testing-latest.tar.gz

echo "Test harness installed"
