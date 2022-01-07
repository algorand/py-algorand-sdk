import base64
import json
import os
import urllib

from behave import (
    given,
    when,
    then,
    step,
)
from algosdk.error import IndexerHTTPError
from algosdk.v2client import indexer


@when(
    "I get the next page using {indexer} to lookup asset balances for {assetid} with {currencygt}, {currencylt}, {limit}"
)
def next_asset_balance(
    context, indexer, assetid, currencygt, currencylt, limit
):
    context.response = context.icls[indexer].asset_balances(
        int(assetid),
        min_balance=int(currencygt),
        max_balance=int(currencylt),
        limit=int(limit),
        next_page=context.response["next-token"],
    )


@when(
    'we make a Lookup Asset Balances call against asset index {index} with limit {limit} afterAddress "{afterAddress:MaybeString}" round {block} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan}'
)
def asset_balance(
    context,
    index,
    limit,
    afterAddress,
    block,
    currencyGreaterThan,
    currencyLessThan,
):
    context.response = context.icl.asset_balances(
        int(index),
        int(limit),
        next_page=None,
        min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan),
        block=int(block),
    )


@when("we make any LookupAssetBalances call")
def asset_balance_any(context):
    context.response = context.icl.asset_balances(123, 10)


@when("I use {indexer} to search for all {assetid} asset transactions")
def icl_asset_txns(context, indexer, assetid):
    context.response = context.icls[indexer].search_asset_transactions(
        int(assetid)
    )


@when(
    'we make a Lookup Asset Transactions call against asset index {index} with NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} address "{address:MaybeString}" addressRole "{addressRole:MaybeString}" ExcluseCloseTo "{excludeCloseTo:MaybeString}" RekeyTo "{rekeyTo:MaybeString}"'
)
def asset_txns(
    context,
    index,
    notePrefixB64,
    txType,
    sigType,
    txid,
    block,
    minRound,
    maxRound,
    limit,
    beforeTime,
    afterTime,
    currencyGreaterThan,
    currencyLessThan,
    address,
    addressRole,
    excludeCloseTo,
    rekeyTo,
):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if address == "none":
        address = None
    if addressRole == "none":
        addressRole = None
    if excludeCloseTo == "none":
        excludeCloseTo = None
    if rekeyTo == "none":
        rekeyTo = None
    context.response = context.icl.search_asset_transactions(
        int(index),
        limit=int(limit),
        next_page=None,
        note_prefix=base64.b64decode(notePrefixB64),
        txn_type=txType,
        sig_type=sigType,
        txid=txid,
        block=int(block),
        min_round=int(minRound),
        max_round=int(maxRound),
        start_time=afterTime,
        end_time=beforeTime,
        min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan),
        address=address,
        address_role=addressRole,
        exclude_close_to=excludeCloseTo,
        rekey_to=rekeyTo,
    )


@when(
    'we make a Lookup Asset Transactions call against asset index {index} with NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} address "{address:MaybeString}" addressRole "{addressRole:MaybeString}" ExcluseCloseTo "{excludeCloseTo:MaybeString}"'
)
def step_impl(
    context,
    index,
    notePrefixB64,
    txType,
    sigType,
    txid,
    block,
    minRound,
    maxRound,
    limit,
    beforeTime,
    afterTime,
    currencyGreaterThan,
    currencyLessThan,
    address,
    addressRole,
    excludeCloseTo,
):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if address == "none":
        address = None
    if addressRole == "none":
        addressRole = None
    if excludeCloseTo == "none":
        excludeCloseTo = None

    context.response = context.icl.search_asset_transactions(
        int(index),
        limit=int(limit),
        next_page=None,
        note_prefix=base64.b64decode(notePrefixB64),
        txn_type=txType,
        sig_type=sigType,
        txid=txid,
        block=int(block),
        min_round=int(minRound),
        max_round=int(maxRound),
        start_time=afterTime,
        end_time=beforeTime,
        min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan),
        address=address,
        address_role=addressRole,
        exclude_close_to=excludeCloseTo,
        rekey_to=None,
    )


@when("we make any LookupAssetTransactions call")
def asset_txns_any(context):
    context.response = context.icl.search_asset_transactions(32)


@when('I use {indexer} to search for all "{accountid}" transactions')
def icl_txns_by_addr(context, indexer, accountid):
    context.response = context.icls[indexer].search_transactions_by_address(
        accountid
    )


@when(
    'we make a Lookup Account Transactions call against account "{account:MaybeString}" with NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index} rekeyTo "{rekeyTo:MaybeString}"'
)
def txns_by_addr(
    context,
    account,
    notePrefixB64,
    txType,
    sigType,
    txid,
    block,
    minRound,
    maxRound,
    limit,
    beforeTime,
    afterTime,
    currencyGreaterThan,
    currencyLessThan,
    index,
    rekeyTo,
):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if rekeyTo == "none":
        rekeyTo = None
    context.response = context.icl.search_transactions_by_address(
        asset_id=int(index),
        limit=int(limit),
        next_page=None,
        note_prefix=base64.b64decode(notePrefixB64),
        txn_type=txType,
        sig_type=sigType,
        txid=txid,
        block=int(block),
        min_round=int(minRound),
        max_round=int(maxRound),
        start_time=afterTime,
        end_time=beforeTime,
        min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan),
        address=account,
        rekey_to=rekeyTo,
    )


@when(
    'we make a Lookup Account Transactions call against account "{account:MaybeString}" with NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index}'
)
def txns_by_addr(
    context,
    account,
    notePrefixB64,
    txType,
    sigType,
    txid,
    block,
    minRound,
    maxRound,
    limit,
    beforeTime,
    afterTime,
    currencyGreaterThan,
    currencyLessThan,
    index,
):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    context.response = context.icl.search_transactions_by_address(
        asset_id=int(index),
        limit=int(limit),
        next_page=None,
        note_prefix=base64.b64decode(notePrefixB64),
        txn_type=txType,
        sig_type=sigType,
        txid=txid,
        block=int(block),
        min_round=int(minRound),
        max_round=int(maxRound),
        start_time=afterTime,
        end_time=beforeTime,
        min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan),
        address=account,
        rekey_to=None,
    )


@when("we make any LookupAccountTransactions call")
def txns_by_addr_any(context):
    context.response = context.icl.search_transactions_by_address(
        "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
    )


@when("I use {indexer} to check the services health")
def icl_health(context, indexer):
    context.response = context.icls[indexer].health()


@then("I receive status code {code}")
def icl_health_check(context, code):
    # An exception is thrown when the code is not 200
    assert int(code) == 200


@when("I use {indexer} to lookup block {number}")
def icl_lookup_block(context, indexer, number):
    context.response = context.icls[indexer].block_info(int(number))


@then(
    'The block was confirmed at {timestamp}, contains {num} transactions, has the previous block hash "{prevHash}"'
)
def icl_block_check(context, timestamp, num, prevHash):
    assert context.response["previous-block-hash"] == prevHash
    assert len(context.response["transactions"]) == int(num)
    assert context.response["timestamp"] == int(timestamp)


@when("we make a Lookup Block call against round {block}")
def lookup_block(context, block):
    context.response = context.icl.block_info(int(block))


@when("we make any LookupBlock call")
def lookup_block_any(context):
    context.response = context.icl.block_info(12)


@when('I use {indexer} to lookup account "{account}" at round {round}')
def icl_lookup_account_at_round(context, indexer, account, round):
    context.response = context.icls[indexer].account_info(account, int(round))


@when(
    'we make a Lookup Account by ID call against account "{account}" with round {block}'
)
def lookup_account(context, account, block):
    context.response = context.icl.account_info(account, int(block))


@when("we make any LookupAccountByID call")
def lookup_account_any(context):
    context.response = context.icl.account_info(
        "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI", 12
    )


@when(
    'I use {indexer} to lookup asset balances for {assetid} with {currencygt}, {currencylt}, {limit} and token "{token}"'
)
def icl_asset_balance(
    context, indexer, assetid, currencygt, currencylt, limit, token
):
    context.response = context.icls[indexer].asset_balances(
        int(assetid),
        min_balance=int(currencygt),
        max_balance=int(currencylt),
        limit=int(limit),
        next_page=token,
    )


def parse_args(assetid):
    t = assetid.split(" ")
    l = {
        "assetid": t[2],
        "currencygt": t[4][:-1],
        "currencylt": t[5][:-1],
        "limit": t[6],
        "token": t[9][1:-1],
    }
    return l


@when("I use {indexer} to lookup asset {assetid}")
def icl_lookup_asset(context, indexer, assetid):
    try:
        context.response = context.icls[indexer].asset_info(int(assetid))
    except:
        icl_asset_balance(context, indexer, **parse_args(assetid))


@then(
    'The asset found has: "{name}", "{units}", "{creator}", {decimals}, "{defaultfrozen}", {total}, "{clawback}"'
)
def check_lookup_asset(
    context, name, units, creator, decimals, defaultfrozen, total, clawback
):
    assert context.response["asset"]["params"]["name"] == name
    assert context.response["asset"]["params"]["unit-name"] == units
    assert context.response["asset"]["params"]["creator"] == creator
    assert context.response["asset"]["params"]["decimals"] == int(decimals)
    assert context.response["asset"]["params"]["default-frozen"] == (
        defaultfrozen == "true"
    )
    assert context.response["asset"]["params"]["total"] == int(total)
    assert context.response["asset"]["params"]["clawback"] == clawback


@when("we make a Lookup Asset by ID call against asset index {index}")
def lookup_asset(context, index):
    context.response = context.icl.asset_info(int(index))


@when("we make any LookupAssetByID call")
def lookup_asset_any(context):
    context.response = context.icl.asset_info(1)


@then("the parsed LookupAssetByID response should have index {index}")
def parse_asset(context, index):
    assert context.response["asset"]["index"] == int(index)


@when(
    "we make a Search Accounts call with assetID {index} limit {limit} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} and round {block}"
)
def search_accounts(
    context, index, limit, currencyGreaterThan, currencyLessThan, block
):
    context.response = context.icl.accounts(
        asset_id=int(index),
        limit=int(limit),
        next_page=None,
        min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan),
        block=int(block),
    )


@when(
    'we make a Search Accounts call with assetID {index} limit {limit} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} round {block} and authenticating address "{authAddr:MaybeString}"'
)
def search_accounts_with_auth_addr(
    context,
    index,
    limit,
    currencyGreaterThan,
    currencyLessThan,
    block,
    authAddr,
):
    if authAddr == "none":
        authAddr = None
    context.response = context.icl.accounts(
        asset_id=int(index),
        limit=int(limit),
        next_page=None,
        min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan),
        block=int(block),
        auth_addr=authAddr,
    )


@when(
    'I use {indexer} to search for an account with {assetid}, {limit}, {currencygt}, {currencylt}, "{auth_addr:MaybeString}", {application_id}, "{include_all:MaybeBool}" and token "{token:MaybeString}"'
)
def icl_search_accounts_with_auth_addr_and_app_id_and_include_all(
    context,
    indexer,
    assetid,
    limit,
    currencygt,
    currencylt,
    auth_addr,
    application_id,
    include_all,
    token,
):
    context.response = context.icls[indexer].accounts(
        asset_id=int(assetid),
        limit=int(limit),
        next_page=token,
        min_balance=int(currencygt),
        max_balance=int(currencylt),
        auth_addr=auth_addr,
        application_id=int(application_id),
        include_all=include_all,
    )


@when(
    'I use {indexer} to search for an account with {assetid}, {limit}, {currencygt}, {currencylt}, "{auth_addr:MaybeString}", {application_id} and token "{token:MaybeString}"'
)
def icl_search_accounts_with_auth_addr_and_app_id(
    context,
    indexer,
    assetid,
    limit,
    currencygt,
    currencylt,
    auth_addr,
    application_id,
    token,
):
    context.response = context.icls[indexer].accounts(
        asset_id=int(assetid),
        limit=int(limit),
        next_page=token,
        min_balance=int(currencygt),
        max_balance=int(currencylt),
        auth_addr=auth_addr,
        application_id=int(application_id),
    )


@when(
    'I use {indexer} to search for an account with {assetid}, {limit}, {currencygt}, {currencylt} and token "{token:MaybeString}"'
)
def icl_search_accounts_legacy(
    context, indexer, assetid, limit, currencygt, currencylt, token
):
    context.response = context.icls[indexer].accounts(
        asset_id=int(assetid),
        limit=int(limit),
        next_page=token,
        min_balance=int(currencygt),
        max_balance=int(currencylt),
    )


@then(
    "I get the next page using {indexer} to search for an account with {assetid}, {limit}, {currencygt} and {currencylt}"
)
def search_accounts_nex(
    context, indexer, assetid, limit, currencygt, currencylt
):
    context.response = context.icls[indexer].accounts(
        asset_id=int(assetid),
        limit=int(limit),
        min_balance=int(currencygt),
        max_balance=int(currencylt),
        next_page=context.response["next-token"],
    )


@then(
    'There are {num}, the first has {pendingrewards}, {rewardsbase}, {rewards}, {withoutrewards}, "{address}", {amount}, "{status}", "{sigtype:MaybeString}"'
)
def check_search_accounts(
    context,
    num,
    pendingrewards,
    rewardsbase,
    rewards,
    withoutrewards,
    address,
    amount,
    status,
    sigtype,
):
    assert len(context.response["accounts"]) == int(num)
    assert context.response["accounts"][0]["pending-rewards"] == int(
        pendingrewards
    )
    assert context.response["accounts"][0].get("rewards-base", 0) == int(
        rewardsbase
    )
    assert context.response["accounts"][0]["rewards"] == int(rewards)
    assert context.response["accounts"][0][
        "amount-without-pending-rewards"
    ] == int(withoutrewards)
    assert context.response["accounts"][0]["address"] == address
    assert context.response["accounts"][0]["amount"] == int(amount)
    assert context.response["accounts"][0]["status"] == status
    assert context.response["accounts"][0].get("sig-type", "") == sigtype


@then(
    'The first account is online and has "{address}", {keydilution}, {firstvalid}, {lastvalid}, "{votekey}", "{selectionkey}"'
)
def check_search_accounts_online(
    context, address, keydilution, firstvalid, lastvalid, votekey, selectionkey
):
    assert context.response["accounts"][0]["status"] == "Online"
    assert context.response["accounts"][0]["address"] == address
    assert context.response["accounts"][0]["participation"][
        "vote-key-dilution"
    ] == int(keydilution)
    assert context.response["accounts"][0]["participation"][
        "vote-first-valid"
    ] == int(firstvalid)
    assert context.response["accounts"][0]["participation"][
        "vote-last-valid"
    ] == int(lastvalid)
    assert (
        context.response["accounts"][0]["participation"][
            "vote-participation-key"
        ]
        == votekey
    )
    assert (
        context.response["accounts"][0]["participation"][
            "selection-participation-key"
        ]
        == selectionkey
    )


@when("we make any SearchAccounts call")
def search_accounts_any(context):
    context.response = context.icl.accounts(asset_id=2)


@when(
    "I get the next page using {indexer} to search for transactions with {limit} and {maxround}"
)
def search_txns_next(context, indexer, limit, maxround):
    context.response = context.icls[indexer].search_transactions(
        limit=int(limit),
        max_round=int(maxround),
        next_page=context.response["next-token"],
    )


@when(
    'I use {indexer} to search for transactions with {limit}, "{noteprefix:MaybeString}", "{txtype:MaybeString}", "{sigtype:MaybeString}", "{txid:MaybeString}", {block}, {minround}, {maxround}, {assetid}, "{beforetime:MaybeString}", "{aftertime:MaybeString}", {currencygt}, {currencylt}, "{address:MaybeString}", "{addressrole:MaybeString}", "{excludecloseto:MaybeString}" and token "{token:MaybeString}"'
)
def icl_search_txns(
    context,
    indexer,
    limit,
    noteprefix,
    txtype,
    sigtype,
    txid,
    block,
    minround,
    maxround,
    assetid,
    beforetime,
    aftertime,
    currencygt,
    currencylt,
    address,
    addressrole,
    excludecloseto,
    token,
):
    context.response = context.icls[indexer].search_transactions(
        asset_id=int(assetid),
        limit=int(limit),
        next_page=token,
        note_prefix=base64.b64decode(noteprefix),
        txn_type=txtype,
        sig_type=sigtype,
        txid=txid,
        block=int(block),
        min_round=int(minround),
        max_round=int(maxround),
        start_time=aftertime,
        end_time=beforetime,
        min_amount=int(currencygt),
        max_amount=int(currencylt),
        address=address,
        address_role=addressrole,
        exclude_close_to=excludecloseto == "true",
    )


@when(
    'I use {indexer} to search for transactions with {limit}, "{noteprefix:MaybeString}", "{txtype:MaybeString}", "{sigtype:MaybeString}", "{txid:MaybeString}", {block}, {minround}, {maxround}, {assetid}, "{beforetime:MaybeString}", "{aftertime:MaybeString}", {currencygt}, {currencylt}, "{address:MaybeString}", "{addressrole:MaybeString}", "{excludecloseto:MaybeString}", {application_id} and token "{token:MaybeString}"'
)
def icl_search_txns_with_app(
    context,
    indexer,
    limit,
    noteprefix,
    txtype,
    sigtype,
    txid,
    block,
    minround,
    maxround,
    assetid,
    beforetime,
    aftertime,
    currencygt,
    currencylt,
    address,
    addressrole,
    excludecloseto,
    application_id,
    token,
):
    context.response = context.icls[indexer].search_transactions(
        asset_id=int(assetid),
        limit=int(limit),
        next_page=token,
        note_prefix=base64.b64decode(noteprefix),
        txn_type=txtype,
        sig_type=sigtype,
        txid=txid,
        block=int(block),
        min_round=int(minround),
        max_round=int(maxround),
        start_time=aftertime,
        end_time=beforetime,
        min_amount=int(currencygt),
        max_amount=int(currencylt),
        address=address,
        address_role=addressrole,
        application_id=int(application_id),
        exclude_close_to=excludecloseto == "true",
    )


@when(
    'we make a Search For Transactions call with account "{account:MaybeString}" NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index} addressRole "{addressRole:MaybeString}" ExcluseCloseTo "{excludeCloseTo:MaybeString}" rekeyTo "{rekeyTo:MaybeString}"'
)
def search_txns(
    context,
    account,
    notePrefixB64,
    txType,
    sigType,
    txid,
    block,
    minRound,
    maxRound,
    limit,
    beforeTime,
    afterTime,
    currencyGreaterThan,
    currencyLessThan,
    index,
    addressRole,
    excludeCloseTo,
    rekeyTo,
):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if account == "none":
        account = None
    if addressRole == "none":
        addressRole = None
    if excludeCloseTo == "none":
        excludeCloseTo = None
    if rekeyTo == "none":
        rekeyTo = None
    context.response = context.icl.search_transactions(
        asset_id=int(index),
        limit=int(limit),
        next_page=None,
        note_prefix=base64.b64decode(notePrefixB64),
        txn_type=txType,
        sig_type=sigType,
        txid=txid,
        block=int(block),
        min_round=int(minRound),
        max_round=int(maxRound),
        start_time=afterTime,
        end_time=beforeTime,
        min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan),
        address=account,
        address_role=addressRole,
        exclude_close_to=excludeCloseTo,
        rekey_to=rekeyTo,
    )


@when(
    'we make a Search For Transactions call with account "{account:MaybeString}" NotePrefix "{notePrefixB64:MaybeString}" TxType "{txType:MaybeString}" SigType "{sigType:MaybeString}" txid "{txid:MaybeString}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime:MaybeString}" afterTime "{afterTime:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index} addressRole "{addressRole:MaybeString}" ExcluseCloseTo "{excludeCloseTo:MaybeString}"'
)
def search_txns(
    context,
    account,
    notePrefixB64,
    txType,
    sigType,
    txid,
    block,
    minRound,
    maxRound,
    limit,
    beforeTime,
    afterTime,
    currencyGreaterThan,
    currencyLessThan,
    index,
    addressRole,
    excludeCloseTo,
):
    if notePrefixB64 == "none":
        notePrefixB64 = ""
    if txType == "none":
        txType = None
    if sigType == "none":
        sigType = None
    if txid == "none":
        txid = None
    if beforeTime == "none":
        beforeTime = None
    if afterTime == "none":
        afterTime = None
    if account == "none":
        account = None
    if addressRole == "none":
        addressRole = None
    if excludeCloseTo == "none":
        excludeCloseTo = None
    context.response = context.icl.search_transactions(
        asset_id=int(index),
        limit=int(limit),
        next_page=None,
        note_prefix=base64.b64decode(notePrefixB64),
        txn_type=txType,
        sig_type=sigType,
        txid=txid,
        block=int(block),
        min_round=int(minRound),
        max_round=int(maxRound),
        start_time=afterTime,
        end_time=beforeTime,
        min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan),
        address=account,
        address_role=addressRole,
        exclude_close_to=excludeCloseTo,
        rekey_to=None,
    )


@when("we make any SearchForTransactions call")
def search_txns_any(context):
    context.response = context.icl.search_transactions(asset_id=2)


@when(
    'I use {indexer} to search for assets with {limit}, {assetidin}, "{creator:MaybeString}", "{name:MaybeString}", "{unit:MaybeString}", and token "{token:MaybeString}"'
)
def icl_search_assets(
    context, indexer, limit, assetidin, creator, name, unit, token
):
    context.response = context.icls[indexer].search_assets(
        limit=int(limit),
        next_page=token,
        creator=creator,
        name=name,
        unit=unit,
        asset_id=int(assetidin),
    )


@then("there are {num} assets in the response, the first is {assetidout}.")
def check_assets(context, num, assetidout):
    assert len(context.response["assets"]) == int(num)
    if int(num) > 0:
        assert context.response["assets"][0]["index"] == int(assetidout)


@when(
    'I use {indexer} to search for applications with {limit}, {application_id}, "{include_all:MaybeBool}" and token "{token:MaybeString}"'
)
def search_applications_include_all(
    context, indexer, limit, application_id, include_all, token
):
    context.response = context.icls[indexer].search_applications(
        application_id=int(application_id),
        limit=int(limit),
        include_all=include_all,
        next_page=token,
    )


@when(
    'I use {indexer} to search for applications with {limit}, {application_id}, and token "{token:MaybeString}"'
)
def search_applications(context, indexer, limit, application_id, token):
    context.response = context.icls[indexer].search_applications(
        application_id=int(application_id), limit=int(limit), next_page=token
    )


@when(
    'I use {indexer} to lookup application with {application_id} and "{include_all:MaybeBool}"'
)
def lookup_application_include_all(
    context, indexer, application_id, include_all
):
    try:
        context.response = context.icls[indexer].applications(
            application_id=int(application_id), include_all=include_all
        )
    except IndexerHTTPError as e:
        context.response = json.loads(str(e))


@when("I use {indexer} to lookup application with {application_id}")
def lookup_application(context, indexer, application_id):
    context.response = context.icls[indexer].applications(
        application_id=int(application_id)
    )


@then('the parsed response should equal "{jsonfile}".')
def step_impl(context, jsonfile):
    loaded_response = None
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    with open(dir_path + "/test/features/resources/" + jsonfile, "rb") as f:
        loaded_response = bytearray(f.read())
    # sort context.response
    def recursively_sort_on_key(dictionary):
        returned_dict = dict()
        for k, v in sorted(dictionary.items()):
            if isinstance(v, dict):
                returned_dict[k] = recursively_sort_on_key(v)
            elif isinstance(v, list) and all(
                isinstance(item, dict) for item in v
            ):
                if all("key" in item.keys() for item in v):
                    from operator import itemgetter

                    returned_dict[k] = sorted(v, key=itemgetter("key"))
                else:
                    sorted_list = list()
                    for item in v:
                        sorted_list.append(recursively_sort_on_key(item))
                    returned_dict[k] = sorted_list
            else:
                returned_dict[k] = v
        return returned_dict

    context.response = recursively_sort_on_key(context.response)
    loaded_response = recursively_sort_on_key(json.loads(loaded_response))
    if context.response != loaded_response:
        print("EXPECTED: " + str(loaded_response))
        print("ACTUAL: " + str(context.response))
    assert context.response == loaded_response


@when(
    'we make a SearchForAssets call with limit {limit} creator "{creator:MaybeString}" name "{name:MaybeString}" unit "{unit:MaybeString}" index {index}'
)
def search_assets(context, limit, creator, name, unit, index):
    if creator == "none":
        creator = None
    if name == "none":
        name = None
    if unit == "none":
        unit = None

    context.response = context.icl.search_assets(
        limit=int(limit),
        next_page=None,
        creator=creator,
        name=name,
        unit=unit,
        asset_id=int(index),
    )


@when("we make any SearchForAssets call")
def search_assets_any(context):
    context.response = context.icl.search_assets(asset_id=2)


@then(
    "the parsed SearchForAssets response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have asset index {assetIndex}"
)
def parse_search_assets(context, roundNum, length, index, assetIndex):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["assets"]) == int(length)
    if int(length) > 0:
        assert context.response["assets"][int(index)]["index"] == int(
            assetIndex
        )


@when("we make any Suggested Transaction Parameters call")
def suggested_any(context):
    context.response = context.acl.suggested_params()


@then(
    "the parsed Suggested Transaction Parameters response should have first round valid of {roundNum}"
)
def parse_suggested(context, roundNum):
    assert context.response.first == int(roundNum)


@then('expect the path used to be "{path}"')
def expect_path(context, path):
    if not isinstance(context.response, dict):
        try:
            context.response = json.loads(context.response)
        except json.JSONDecodeError:
            pass
    exp_path, exp_query = urllib.parse.splitquery(path)
    exp_query = urllib.parse.parse_qs(exp_query)

    actual_path, actual_query = urllib.parse.splitquery(
        context.response["path"]
    )
    actual_query = urllib.parse.parse_qs(actual_query)
    assert exp_path == actual_path.replace("%3A", ":")
    assert exp_query == actual_query


@then('we expect the path used to be "{path}"')
def we_expect_path(context, path):
    expect_path(context, path)


# TODO: make this actually expect an error
@then('expect error string to contain "{err:MaybeString}"')
def expect_error(context, err):
    pass


@given(
    'indexer client {index} at "{address}" port {port} with token "{token}"'
)
def indexer_client(context, index, address, port, token):
    if not hasattr(context, "icls"):
        context.icls = dict()
    context.icls[index] = indexer.IndexerClient(
        token, "http://" + address + ":" + str(port)
    )


@when("we make a SearchForApplications call with {application_id} and {round}")
def search_applications(context, application_id, round):
    context.response = context.icl.search_applications(
        application_id=int(application_id), round=int(round)
    )


@when("we make a LookupApplications call with {application_id} and {round}")
def lookup_applications(context, application_id, round):
    context.response = context.icl.applications(
        application_id=int(application_id), round=int(round)
    )
