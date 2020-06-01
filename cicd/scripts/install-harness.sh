#!/usr/bin/env bash

set -e

# Reset test harness
rm -rf test-harness

BRANCH=${ALGORAND_SDK_TESTING_BRANCH-'develop'}
GITHUB_ORG=${ALGORAND_SDK_TESTING_ORG-'algorand'}

git clone --single-branch --branch ${BRANCH} "https://github.com/${GITHUB_ORG}/algorand-sdk-testing.git" test-harness

## Copy feature files into the project resources
mkdir -p test/features
cp -r test-harness/features/* test/features
