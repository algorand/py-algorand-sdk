import json
from algosdk.v2client import indexer


# example: CREATE_INDEXER_CLIENT
# instantiate indexer client
indexer_host = "http://localhost:8980"
indexer_token = "a" * 64
myindexer = indexer.IndexerClient(
    indexer_token=indexer_token, indexer_address=indexer_host
)
# example: CREATE_INDEXER_CLIENT

# example: INDEXER_LOOKUP_ASSET
# lookup a single asset
asset_id = 2044572
# by passing include_all, we specify that we want to see deleted assets as well
response = myindexer.asset_info(asset_id, include_all=True)
print(f"Asset Info: {json.dumps(response, indent=2,)}")
# example: INDEXER_LOOKUP_ASSET

# example: INDEXER_SEARCH_MIN_AMOUNT
response = myindexer.search_transactions(
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
    response = myindexer.search_transactions(
        min_amount=10, min_round=1000, max_round=1500
    )

    has_results = len(response["transactions"]) > 0

    if has_results:
        nexttoken = response["next-token"]
        print(f"Tranastion on page {page}: " + json.dumps(response, indent=2))

    page += 1
# example: INDEXER_PAGINATE_RESULTS

# example: INDEXER_PREFIX_SEARCH
note_prefix = "showing prefix".encode()
response = myindexer.search_transactions(note_prefix=note_prefix)
print(f"result: {json.dumps(response, indent=2)}")
# example: INDEXER_PREFIX_SEARCH
