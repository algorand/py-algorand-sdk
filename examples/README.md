Algorand Python SDK Examples
----------------------------

This directory contains examples of how to use the Algorand Python SDK. 

Assuming a sandboxed node is running locally, any example can be run with the following command:

```sh
    python3 <example_name>.py
```

The post-quantum example, `falcon.py`, has two extra requirements: the Falcon-1024 implementation from the `algorand-falcon` package (`pip install algorand-falcon`, not a dependency of the SDK), and a node running the `future` consensus version. It skips itself when either is missing.

