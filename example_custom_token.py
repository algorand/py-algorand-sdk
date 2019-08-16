# Example of accesing a remote API with a custom token key.
#
# In this case, the API is expecting the key "X-API-Key" instead of the
# default "X-Algo-API-Token". This is done by using a dict with our custom
# key, instead of a string, as the token.

from algosdk import algod

algod_address = ''
algod_token = {
   'X-API-Key': '',
    'content-type' : 'application/json'
}


def main():

    acl = algod.AlgodClient(algod_token, algod_address)
    print(acl.versions())

main()