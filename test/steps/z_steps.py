"""
Formerly this belonged to:

    And I can dig into the resulting atomic transaction execution tree with path "0,0,0"
    And I can dig into the resulting atomic transaction execution tree with path "0,2,0"
    And I can dig into the resulting atomic transaction execution tree with path "1,2,0"

cf: https://github.com/algorand/algorand-sdk-testing/pull/156/commits/a691cecc9bd14c4eb7054c434f519062da2bfc18

@then(
    'I can dig into the resulting atomic transaction execution tree with path "{path}"'
)
def digging_the_inner_txns(context, path):
    d = context.atomic_transaction_composer_return.abi_results
    for i, p in enumerate(path.split(",")):
        idx = int(p)
        d = d["inner-txns"][idx] if i else d[idx].tx_info
"""
