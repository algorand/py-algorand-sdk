# Example of accesing a remote API with a custom token key.
#
# In this case, the API is expecting the key "X-API-Key" instead of the
# default "X-Algo-API-Token". This is done by using a dict with our custom
# key, instead of a string, as the token.

from algosdk import algod

algod_address = "http://127.0.0.1:8080"
algod_token = {
   'X-API-Key': 'e48a9bbe064a08f19cde9f0f1b589c1188b24e5059bc661b31bd20b4c8fa4ce7',
}

def main():

    acl = algod.AlgodClient(algod_token, algod_address)
    print(acl.versions())

main()