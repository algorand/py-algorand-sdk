#!/usr/bin/env bash

set -e

cicd/scripts/install-harness.sh

# Build SDK testing environment
docker build -t py-sdk-testing -f Dockerfile "$(pwd)"

cicd/scripts/start-harness.sh

# Launch SDK testing
docker run -it \
     --network host \
     py-sdk-testing:latest 
