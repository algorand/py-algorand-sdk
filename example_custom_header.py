# Example of accesing a remote API with a custom token key.
#
# In this case, the API is expecting the key "X-API-Key" instead of the
# default "X-Algo-API-Token". This is done by using a dict with our custom
# key, instead of a string, as the token.

from algosdk import algod

algod_address = "https://......"
algod_token = ""
headers = {
   "X-API-Key": "#######",
}


def main():
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    try:
        status = algod_client.status()
    except Exception as e:
        print("Failed to get algod status: {}".format(e))

    if status:
        print("algod last round: {}".format(status.get("lastRound")))
        print("algod time since last round: {}".format(
              status.get("timeSinceLastRound")))
        print("algod catchup: {}".format(status.get("catchupTime")))
        print("algod latest version: {}".format(
              status.get("lastConsensusVersion")))

    # Retrieve latest block information
    last_round = algod_client.status().get("lastRound")
    print("####################")
    block = algod_client.block_info(last_round)
    print(block)


main()
