#!/usr/bin/env bash

set -e

rm -rf temp
rm -rf test/cucumber/features
git clone --single-branch --branch templates https://github.com/algorand/algorand-sdk-testing.git temp

cp test/cucumber/docker/sdk.py temp/docker
mv temp/features test/cucumber/features

docker build -t sdk-testing -f test/cucumber/docker/Dockerfile "$(pwd)"

docker run -it \
     -v "$(pwd)":/opt/py-algorand-sdk \
     sdk-testing:latest 
