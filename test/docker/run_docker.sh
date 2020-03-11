#!/usr/bin/env bash

set -e

docker build -t sdk-testing -f test/docker/Dockerfile "$(pwd)"

docker run -it \
     -v "$(pwd)":/opt/py-algorand-sdk \
     sdk-testing:latest 
