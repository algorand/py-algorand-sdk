#!/usr/bin/env bash

# Start test harness environment
./test-harness/scripts/up.sh

while [ $(curl -sL -w "%{http_code}\\n" "http://localhost:59999/v2/accounts" -o /dev/null --connect-timeout 3 --max-time 5) -ne "200" ]
do
  sleep 1
done
