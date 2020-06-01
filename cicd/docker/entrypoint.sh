#!/bin/bash

pip3 install .

# This is done to ignore the first two arguements
# passed by mule (bash, -c)
$3
