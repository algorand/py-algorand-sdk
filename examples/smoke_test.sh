#!/usr/bin/env bash

export ALGOD_PORT="60000"
export INDEXER_PORT="59999"
export KMD_PORT="60001"


# Loop over all files in the directory
for file in *; do
    # Check if the file ends with ".py"
    if [[ $file == *.py ]]; then
        # Check if the filename is not "utils.py"
        if [[ $file != "utils.py" ]]; then
            # Call the file using Python
            python3 "$file"
        fi
    fi
done
