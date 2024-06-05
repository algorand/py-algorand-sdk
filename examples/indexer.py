import json
from algosdk import transaction
from algosdk.v2client import indexer
from utils import (
    get_accounts,
    get_algod_client,
    get_indexer_client,
    indexer_wait_for_round,
)


# example: INDEXER_CREATE_CLIENT
# instantiate indexer client
indexer_host = "http://localhost:8980"
indexer_token = "a" * 64
indexer_client = indexer.IndexerClient(
    indexer_token=indexer_token, indexer_address=indexer_host
)
# example: INDEXER_CREATE_CLIENT

indexer_client = get_indexer_client()

algod_client = get_algod_client()
acct = get_accounts().pop()

# create an asset we can lookup
actxn = transaction.AssetCreateTxn(
    acct.address,
    algod_client.suggested_params(),
    100,
    0,
    False,
    manager=acct.address,
    unit_name="example",
    asset_name="example asset",
)

txid = algod_client.send_transaction(actxn.sign(acct.private_key))
res = transaction.wait_for_confirmation(algod_client, txid, 4)
asset_id = res["asset-index"]

ptxn = transaction.PaymentTxn(
    acct.address, algod_client.suggested_params(), acct.address, 1000
)
transaction.wait_for_confirmation(
    algod_client, algod_client.send_transaction(ptxn.sign(acct.private_key)), 4
)

# allow indexer to catch up
indexer_wait_for_round(indexer_client, res["confirmed-round"], 30)

# example: INDEXER_LOOKUP_ASSET
# lookup a single asset
# by passing include_all, we specify that we want to see deleted assets as well
response = indexer_client.asset_info(asset_id, include_all=True)
print(f"Asset Info: {json.dumps(response, indent=2,)}")
# example: INDEXER_LOOKUP_ASSET

# example: INDEXER_SEARCH_MIN_AMOUNT
response = indexer_client.search_transactions(
    min_amount=10, min_round=1000, max_round=1500
)
print(f"Transaction results: {json.dumps(response, indent=2)}")
# example: INDEXER_SEARCH_MIN_AMOUNT

# example: INDEXER_PAGINATE_RESULTS

nexttoken = ""
has_results = True
page = 0

# loop using next_page to paginate until there are
# no more transactions in the response
while has_results:
    response = indexer_client.search_transactions(
        min_amount=10, min_round=1000, max_round=1500, next_page=nexttoken
    )

    has_results = len(response["transactions"]) > 0

    if has_results:
        nexttoken = response["next-token"]
        print(f"Tranastion on page {page}: " + json.dumps(response, indent=2))

    page += 1
# example: INDEXER_PAGINATE_RESULTS

# example: INDEXER_PREFIX_SEARCH
note_prefix = "showing prefix".encode()
response = indexer_client.search_transactions(note_prefix=note_prefix)
print(f"result: {json.dumps(response, indent=2)}")
# example: INDEXER_PREFIX_SEARCH
