import base64
import json
import os
import re
import urllib
import unittest
from datetime import datetime
from pathlib import Path
import pytest
from typing import List, Union
from urllib.request import Request, urlopen

# TODO: This file is WAY TOO BIG. Break it up into logically related chunks.

from behave import (
    given,
    when,
    then,
    register_type,
    step,
)  # pylint: disable=no-name-in-module

from glom import glom
import parse

from algosdk import (
    abi,
    account,
    atomic_transaction_composer,
    dryrun_results,
    encoding,
    error,
    logic,
    mnemonic,
)
from algosdk.abi.contract import NetworkInfo
from algosdk.error import ABITypeError, AlgodHTTPError, IndexerHTTPError
from algosdk.future import transaction
from algosdk.v2client import *
from algosdk.v2client.models import (
    DryrunRequest,
    DryrunSource,
    Account,
    ApplicationLocalState,
)
from algosdk.testing.dryrun import DryrunTestCaseMixin

from test.steps.steps import token as daemon_token
from test.steps.steps import algod_port


@parse.with_pattern(r".*")
def parse_string(text):
    return text


register_type(MaybeString=parse_string)


@parse.with_pattern(r"true|false")
def parse_bool(value):
    if value not in ("true", "false"):
        raise ValueError("Unknown value for include_all: {}".format(value))
    return value == "true"


register_type(MaybeBool=parse_bool)


@given("mock server recording request paths")
def setup_mockserver(context):
    context.url = "http://127.0.0.1:" + str(context.path_server_port)
    context.acl = algod.AlgodClient("algod_token", context.url)
    context.icl = indexer.IndexerClient("indexer_token", context.url)


@given('mock http responses in "{jsonfiles}" loaded from "{directory}"')
def mock_response(context, jsonfiles, directory):
    context.url = "http://127.0.0.1:" + str(context.response_server_port)
    context.acl = algod.AlgodClient("algod_token", context.url)
    context.icl = indexer.IndexerClient("indexer_token", context.url)

    # The mock server writes this response to a file, on a regular request
    # that file is read.
    # It's an interesting approach, but currently doesn't support setting
    # the content type, or different return codes. This will require a bit
    # of extra work when/if we support the different error cases.
    #
    # Take a look at 'environment.py' to see the mock servers.
    req = Request(
        context.url + "/mock/" + directory + "/" + jsonfiles, method="GET"
    )
    urlopen(req)


@given(
    'mock http responses in "{filename}" loaded from "{directory}" with status {status}.'
)
def step_impl(context, filename, directory, status):
    context.expected_status_code = int(status)
    with open("test/features/resources/mock_response_status", "w") as f:
        f.write(status)
    mock_response(context, filename, directory)
    f = open("test/features/resources/mock_response_path", "r")
    mock_response_path = f.read()
    f.close()
    f = open("test/features/resources/" + mock_response_path, "r")
    expected_mock_response = f.read()
    f.close()
    expected_mock_response = bytes(expected_mock_response, "ascii")
    context.expected_mock_response = json.loads(expected_mock_response)


def validate_error(context, err):
    if context.expected_status_code != 200:
        if context.expected_status_code == 500:
            assert context.expected_mock_response["message"] == err.args[0], (
                context.expected_mock_response,
                err.args[0],
            )
        else:
            raise NotImplementedError(
                "test does not know how to validate status code "
                + context.expected_status_code
            )
    else:
        raise err


@when('we make any "{client}" call to "{endpoint}".')
def step_impl(context, client, endpoint):
    # with the current implementation of mock responses, there is no need to do an 'endpoint' lookup
    if client == "indexer":
        try:
            context.response = context.icl.health()
        except error.IndexerHTTPError as err:
            validate_error(context, err)
    elif client == "algod":
        try:
            context.response = context.acl.status()
        except error.AlgodHTTPError as err:
            validate_error(context, err)
    else:
        raise NotImplementedError('did not recognize client "' + client + '"')


@then("the parsed response should equal the mock response.")
def step_impl(context):
    if context.expected_status_code == 200:
        assert context.expected_mock_response == context.response


@when(
    'we make a Pending Transaction Information against txid "{txid}" with format "{response_format}"'
)
def pending_txn_info(context, txid, response_format):
    context.response = context.acl.pending_transaction_info(
        txid, response_format=response_format
    )


@when(
    'we make a Pending Transaction Information with max {max} and format "{response_format}"'
)
def pending_txn_with_max(context, max, response_format):
    context.response = context.acl.pending_transactions(
        int(max), response_format=response_format
    )


@when("we make any Pending Transactions Information call")
def pending_txn_any(context):
    context.response = context.acl.pending_transactions(
        100, response_format="msgpack"
    )


@when("we make any Pending Transaction Information call")
def pending_txn_any2(context):
    context.response = context.acl.pending_transaction_info(
        "sdfsf", response_format="msgpack"
    )


@then(
    'the parsed Pending Transaction Information response should have sender "{sender}"'
)
def parse_pending_txn(context, sender):
    context.response = json.loads(context.response)
    assert (
        encoding.encode_address(
            base64.b64decode(context.response["txn"]["txn"]["snd"])
        )
        == sender
    )


@then(
    'the parsed Pending Transactions Information response should contain an array of len {length} and element number {idx} should have sender "{sender}"'
)
def parse_pending_txns(context, length, idx, sender):
    context.response = json.loads(context.response)
    assert len(context.response["top-transactions"]) == int(length)
    assert (
        encoding.encode_address(
            base64.b64decode(
                context.response["top-transactions"][int(idx)]["txn"]["snd"]
            )
        )
        == sender
    )


@when(
    'we make a Pending Transactions By Address call against account "{account}" and max {max} and format "{response_format}"'
)
def pending_txns_by_addr(context, account, max, response_format):
    context.response = context.acl.pending_transactions_by_address(
        account, limit=int(max), response_format=response_format
    )


@when("we make any Pending Transactions By Address call")
def pending_txns_by_addr_any(context):
    context.response = context.acl.pending_transactions_by_address(
        "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI",
        response_format="msgpack",
    )


@then(
    'the parsed Pending Transactions By Address response should contain an array of len {length} and element number {idx} should have sender "{sender}"'
)
def parse_pend_by_addr(context, length, idx, sender):
    context.response = json.loads(context.response)
    assert len(context.response["top-transactions"]) == int(length)
    assert (
        encoding.encode_address(
            base64.b64decode(
                context.response["top-transactions"][int(idx)]["txn"]["snd"]
            )
        )
        == sender
    )


@when("we make any Send Raw Transaction call")
def send_any(context):
    context.response = context.acl.send_raw_transaction("Bg==")


@then('the parsed Send Raw Transaction response should have txid "{txid}"')
def parsed_send(context, txid):
    assert context.response == txid


@when("we make any Node Status call")
def status_any(context):
    context.response = context.acl.status()


@then("the parsed Node Status response should have a last round of {roundNum}")
def parse_status(context, roundNum):
    assert context.response["last-round"] == int(roundNum)


@when("we make a Status after Block call with round {block}")
def status_after(context, block):
    context.response = context.acl.status_after_block(int(block))


@when("we make any Status After Block call")
def status_after_any(context):
    context.response = context.acl.status_after_block(3)


@then(
    "the parsed Status After Block response should have a last round of {roundNum}"
)
def parse_status_after(context, roundNum):
    assert context.response["last-round"] == int(roundNum)


@when("we make any Ledger Supply call")
def ledger_any(context):
    context.response = context.acl.ledger_supply()


@then(
    "the parsed Ledger Supply response should have totalMoney {tot} onlineMoney {online} on round {roundNum}"
)
def parse_ledger(context, tot, online, roundNum):
    assert context.response["online-money"] == int(online)
    assert context.response["total-money"] == int(tot)
    assert context.response["current_round"] == int(roundNum)


@when(
    'we make an Account Information call against account "{account}" with exclude "{exclude:MaybeString}"'
)
def acc_info(context, account, exclude):
    context.response = context.acl.account_info(account, exclude=exclude)


@when('we make an Account Information call against account "{account}"')
def acc_info(context, account):
    context.response = context.acl.account_info(account)


@when("we make any Account Information call")
def acc_info_any(context):
    context.response = context.acl.account_info(
        "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
    )


@then(
    'the parsed Account Information response should have address "{address}"'
)
def parse_acc_info(context, address):
    assert context.response["address"] == address


@when(
    'we make an Account Asset Information call against account "{account}" assetID {assetID}'
)
def acc_asset_info(context, account, assetID):
    context.response = context.acl.account_asset_info(account, assetID)


@when(
    'we make an Account Application Information call against account "{account}" applicationID {applicationID}'
)
def acc_application_info(context, account, applicationID):
    context.response = context.acl.account_application_info(
        account, applicationID
    )


@when("we make a GetAssetByID call for assetID {asset_id}")
def asset_info(context, asset_id):
    context.response = context.acl.asset_info(int(asset_id))


@when("we make a GetApplicationByID call for applicationID {app_id}")
def application_info(context, app_id):
    context.response = context.acl.application_info(int(app_id))


@when(
    'we make a Get Block call against block number {block} with format "{response_format}"'
)
def block(context, block, response_format):
    context.response = context.acl.block_info(
        int(block), response_format=response_format
    )


@when("we make any Get Block call")
def block_any(context):
    context.response = context.acl.block_info(3, response_format="msgpack")


@then('the parsed Get Block response should have rewards pool "{pool}"')
def parse_block(context, pool):
    context.response = json.loads(context.response)
    assert context.response["block"]["rwd"] == pool


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


@then(
    'There are {numaccounts} with the asset, the first is "{account}" has "{isfrozen}" and {amount}'
)
def check_asset_balance(context, numaccounts, account, isfrozen, amount):
    assert len(context.response["balances"]) == int(numaccounts)
    assert context.response["balances"][0]["address"] == account
    assert context.response["balances"][0]["amount"] == int(amount)
    assert context.response["balances"][0]["is-frozen"] == (isfrozen == "true")


@when(
    'we make a Lookup Asset Balances call against asset index {index} with limit {limit} afterAddress "{afterAddress:MaybeString}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan}'
)
def asset_balance(
    context,
    index,
    limit,
    afterAddress,
    currencyGreaterThan,
    currencyLessThan,
):
    context.response = context.icl.asset_balances(
        int(index),
        int(limit),
        next_page=None,
        min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan),
    )


@when("we make any LookupAssetBalances call")
def asset_balance_any(context):
    context.response = context.icl.asset_balances(123, 10)


@then(
    'the parsed LookupAssetBalances response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have address "{address}" amount {amount} and frozen state "{frozenState}"'
)
def parse_asset_balance(
    context, roundNum, length, idx, address, amount, frozenState
):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["balances"]) == int(length)
    assert context.response["balances"][int(idx)]["address"] == address
    assert context.response["balances"][int(idx)]["amount"] == int(amount)
    assert context.response["balances"][int(idx)]["is-frozen"] == (
        frozenState == "true"
    )


@when(
    'we make a LookupAccountAssets call with accountID "{account}" assetID {asset_id} includeAll "{includeAll:MaybeBool}" limit {limit} next "{next:MaybeString}"'
)
def lookup_account_assets(context, account, asset_id, includeAll, limit, next):
    context.response = context.icl.lookup_account_assets(
        account,
        asset_id=int(asset_id),
        include_all=includeAll,
        limit=int(limit),
        next_page=next,
    )


@when(
    'we make a LookupAccountCreatedAssets call with accountID "{account}" assetID {asset_id} includeAll "{includeAll:MaybeBool}" limit {limit} next "{next:MaybeString}"'
)
def lookup_account_created_assets(
    context, account, asset_id, includeAll, limit, next
):
    context.response = context.icl.lookup_account_asset_by_creator(
        account,
        asset_id=int(asset_id),
        include_all=includeAll,
        limit=int(limit),
        next_page=next,
    )


@when(
    'we make a LookupAccountAppLocalStates call with accountID "{account}" applicationID {application_id} includeAll "{includeAll:MaybeBool}" limit {limit} next "{next:MaybeString}"'
)
def lookup_account_applications(
    context, account, application_id, includeAll, limit, next
):
    context.response = context.icl.lookup_account_application_local_state(
        account,
        application_id=int(application_id),
        include_all=includeAll,
        limit=int(limit),
        next_page=next,
    )


@when(
    'we make a LookupAccountCreatedApplications call with accountID "{account}" applicationID {application_id} includeAll "{includeAll:MaybeBool}" limit {limit} next "{next:MaybeString}"'
)
def lookup_account_created_applications(
    context, account, application_id, includeAll, limit, next
):
    context.response = context.icl.lookup_account_application_by_creator(
        account,
        application_id=int(application_id),
        include_all=includeAll,
        limit=int(limit),
        next_page=next,
    )


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


@then(
    'the parsed LookupAssetTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"'
)
def parse_asset_tns(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    assert context.response["transactions"][int(idx)]["sender"] == sender


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


@then(
    'the parsed LookupAccountTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"'
)
def parse_txns_by_addr(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(idx)]["sender"] == sender


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


@then(
    'the parsed LookupBlock response should have previous block hash "{prevHash}"'
)
def parse_lookup_block(context, prevHash):
    assert context.response["previous-block-hash"] == prevHash


@then(
    'The account has {num} assets, the first is asset {index} has a frozen status of "{frozen}" and amount {units}.'
)
def lookup_account_check(context, num, index, frozen, units):
    assert len(context.response["account"]["assets"]) == int(num)
    assert context.response["account"]["assets"][0]["asset-id"] == int(index)
    assert context.response["account"]["assets"][0]["is-frozen"] == (
        frozen == "true"
    )
    assert context.response["account"]["assets"][0]["amount"] == int(units)


@then(
    'The account created {num} assets, the first is asset {index} is named "{name}" with a total amount of {total} "{unit}"'
)
def lookup_account_check_created(context, num, index, name, total, unit):
    assert len(context.response["account"]["created-assets"]) == int(num)
    assert context.response["account"]["created-assets"][0]["index"] == int(
        index
    )
    assert (
        context.response["account"]["created-assets"][0]["params"]["name"]
        == name
    )
    assert (
        context.response["account"]["created-assets"][0]["params"]["unit-name"]
        == unit
    )
    assert context.response["account"]["created-assets"][0]["params"][
        "total"
    ] == int(total)


@then(
    "The account has {μalgos} μalgos and {num} assets, {assetid} has {assetamount}"
)
def lookup_account_check_holdings(context, μalgos, num, assetid, assetamount):
    assert context.response["account"]["amount"] == int(μalgos)
    assert len(context.response["account"].get("assets", [])) == int(num)
    if int(num) > 0:
        assets = context.response["account"]["assets"]
        for a in assets:
            if a["asset-id"] == int(assetid):
                assert a["amount"] == int(assetamount)


@when('I use {indexer} to lookup account "{account}" at round {round}')
def icl_lookup_account_at_round(context, indexer, account, round):
    context.response = context.icls[indexer].account_info(account, int(round))


@when(
    'we make a Lookup Account by ID call against account "{account}" with round {block}'
)
def lookup_account(context, account, block):
    context.response = context.icl.account_info(account, int(block))


@when(
    'we make a Lookup Account by ID call against account "{account}" with exclude "{exclude:MaybeString}"'
)
def lookup_account(context, account, exclude):
    context.response = context.icl.account_info(account, exclude=exclude)


@when("we make any LookupAccountByID call")
def lookup_account_any(context):
    context.response = context.icl.account_info(
        "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI", 12
    )


@then('the parsed LookupAccountByID response should have address "{address}"')
def parse_account(context, address):
    assert context.response["account"]["address"] == address


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


@when("we make a LookupApplications call with applicationID {app_id}")
def lookup_application(context, app_id):
    context.response = context.icl.applications(int(app_id))


@when(
    'we make a LookupApplicationLogsByID call with applicationID {app_id} limit {limit} minRound {min_round} maxRound {max_round} nextToken "{next_token:MaybeString}" sender "{sender:MaybeString}" and txID "{txid:MaybeString}"'
)
def lookup_application_logs(
    context, app_id, limit, min_round, max_round, next_token, sender, txid
):
    context.response = context.icl.application_logs(
        int(app_id),
        limit=int(limit),
        min_round=int(min_round),
        max_round=int(max_round),
        next_page=next_token,
        sender_addr=sender,
        txid=txid,
    )


@when("we make a SearchForApplications call with applicationID {app_id}")
def search_application(context, app_id):
    context.response = context.icl.search_applications(int(app_id))


@when('we make a SearchForApplications call with creator "{creator}"')
def search_application(context, creator):
    context.response = context.icl.search_applications(creator=creator)


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
def search_accounts(
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


@when('we make a Search Accounts call with exclude "{exclude:MaybeString}"')
def search_accounts(
    context,
    exclude,
):
    context.response = context.icl.accounts(exclude=exclude)


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


@then(
    'the parsed SearchAccounts response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have address "{address}"'
)
def parse_accounts(context, roundNum, length, index, address):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["accounts"]) == int(length)
    if int(length) > 0:
        assert context.response["accounts"][int(index)]["address"] == address


@when(
    'the parsed SearchAccounts response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have authorizing address "{authAddr:MaybeString}"'
)
def parse_accounts_auth(context, roundNum, length, index, authAddr):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["accounts"]) == int(length)
    if int(length) > 0:
        assert (
            context.response["accounts"][int(index)]["auth-addr"] == authAddr
        )


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


@then(
    'there are {num} transactions in the response, the first is "{txid:MaybeString}".'
)
def check_transactions(context, num, txid):
    assert len(context.response["transactions"]) == int(num)
    if int(num) > 0:
        assert context.response["transactions"][0]["id"] == txid


@then('Every transaction has tx-type "{txtype}"')
def check_transaction_types(context, txtype):
    for txn in context.response["transactions"]:
        assert txn["tx-type"] == txtype


@then('Every transaction has sig-type "{sigtype}"')
def check_sig_types(context, sigtype):
    for txn in context.response["transactions"]:
        if sigtype == "lsig":
            assert list(txn["signature"].keys())[0] == "logicsig"
        if sigtype == "msig":
            assert list(txn["signature"].keys())[0] == "multisig"
        if sigtype == "sig":
            assert list(txn["signature"].keys())[0] == sigtype


@then("Every transaction has round >= {minround}")
def check_minround(context, minround):
    for txn in context.response["transactions"]:
        assert txn["confirmed-round"] >= int(minround)


@then("Every transaction has round <= {maxround}")
def check_maxround(context, maxround):
    for txn in context.response["transactions"]:
        assert txn["confirmed-round"] <= int(maxround)


@then("Every transaction has round {block}")
def check_round(context, block):
    for txn in context.response["transactions"]:
        assert txn["confirmed-round"] == int(block)


@then("Every transaction works with asset-id {assetid}")
def check_assetid(context, assetid):
    for txn in context.response["transactions"]:
        if "asset-config-transaction" in txn:
            subtxn = txn["asset-config-transaction"]
        else:
            subtxn = txn["asset-transfer-transaction"]
        assert subtxn["asset-id"] == int(assetid) or txn[
            "created-asset-index"
        ] == int(assetid)


@then('Every transaction is older than "{before}"')
def check_before(context, before):
    for txn in context.response["transactions"]:
        t = datetime.fromisoformat(before.replace("Z", "+00:00"))
        assert txn["round-time"] <= datetime.timestamp(t)


@then('Every transaction is newer than "{after}"')
def check_after(context, after):
    t = True
    for txn in context.response["transactions"]:
        t = datetime.fromisoformat(after.replace("Z", "+00:00"))
        if not txn["round-time"] >= datetime.timestamp(t):
            t = False
    assert t


@then("Every transaction moves between {currencygt} and {currencylt} currency")
def check_currency(context, currencygt, currencylt):
    for txn in context.response["transactions"]:
        amt = 0
        if "asset-transfer-transaction" in txn:
            amt = txn["asset-transfer-transaction"]["amount"]
        else:
            amt = txn["payment-transaction"]["amount"]
        if int(currencygt) == 0:
            if int(currencylt) > 0:
                assert amt <= int(currencylt)
        else:
            if int(currencylt) > 0:
                assert int(currencygt) <= amt <= int(currencylt)
            else:
                assert int(currencygt) <= amt


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


@then(
    'the parsed SearchForTransactions response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have sender "{sender}"'
)
def parse_search_txns(context, roundNum, length, index, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(index)]["sender"] == sender


@when(
    'the parsed SearchForTransactions response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have rekey-to "{rekeyTo:MaybeString}"'
)
def step_impl(context, roundNum, length, index, rekeyTo):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert (
            context.response["transactions"][int(index)]["rekey-to"] == rekeyTo
        )


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


@given('a signing account with address "{address}" and mnemonic "{mnemonic}"')
def signing_account(context, address, mnemonic):
    context.signing_mnemonic = mnemonic


@given(
    'suggested transaction parameters fee {fee}, flat-fee "{flat_fee:MaybeBool}", first-valid {first_valid}, last-valid {last_valid}, genesis-hash "{genesis_hash}", genesis-id "{genesis_id}"'
)
def suggested_transaction_parameters(
    context, fee, flat_fee, first_valid, last_valid, genesis_hash, genesis_id
):
    context.suggested_params = transaction.SuggestedParams(
        fee=int(fee),
        flat_fee=flat_fee,
        first=int(first_valid),
        last=int(last_valid),
        gh=genesis_hash,
        gen=genesis_id,
    )


@when(
    'I build a keyreg transaction with sender "{sender}", nonparticipation "{nonpart:MaybeBool}", vote first {vote_first}, vote last {vote_last}, key dilution {key_dilution}, vote public key "{vote_pk:MaybeString}", selection public key "{selection_pk:MaybeString}", and state proof public key "{state_proof_pk:MaybeString}"'
)
def step_impl(
    context,
    sender,
    nonpart,
    vote_first,
    vote_last,
    key_dilution,
    vote_pk,
    selection_pk,
    state_proof_pk,
):
    if nonpart:
        context.transaction = transaction.KeyregNonparticipatingTxn(
            sender, context.suggested_params
        )
        return

    if len(vote_pk) == 0:
        vote_pk = None
    if len(selection_pk) == 0:
        selection_pk = None
    if len(state_proof_pk) == 0:
        state_proof_pk = None

    if vote_pk is None and selection_pk is None and state_proof_pk is None:
        context.transaction = transaction.KeyregOfflineTxn(
            sender, context.suggested_params
        )
        return

    context.transaction = transaction.KeyregOnlineTxn(
        sender,
        context.suggested_params,
        vote_pk,
        selection_pk,
        int(vote_first),
        int(vote_last),
        int(key_dilution),
        sprfkey=state_proof_pk,
    )


@given("suggested transaction parameters from the algod v2 client")
def get_sp_from_algod(context):
    context.suggested_params = context.app_acl.suggested_params()


def operation_string_to_enum(operation):
    if operation == "call":
        return transaction.OnComplete.NoOpOC
    elif operation == "create":
        return transaction.OnComplete.NoOpOC
    elif operation == "noop":
        return transaction.OnComplete.NoOpOC
    elif operation == "update":
        return transaction.OnComplete.UpdateApplicationOC
    elif operation == "optin":
        return transaction.OnComplete.OptInOC
    elif operation == "delete":
        return transaction.OnComplete.DeleteApplicationOC
    elif operation == "clear":
        return transaction.OnComplete.ClearStateOC
    elif operation == "closeout":
        return transaction.OnComplete.CloseOutOC
    else:
        raise NotImplementedError(
            "no oncomplete enum for operation " + operation
        )


def split_and_process_app_args(in_args):
    split_args = in_args.split(",")
    sub_args = [sub_arg.split(":") for sub_arg in split_args]
    app_args = []
    for sub_arg in sub_args:
        if len(sub_arg) == 1:  # assume int
            app_args.append(int(sub_arg[0]))
        elif sub_arg[0] == "str":
            app_args.append(bytes(sub_arg[1], "ascii"))
        elif sub_arg[0] == "b64":
            app_args.append(base64.decodebytes(sub_arg[1].encode()))
        elif sub_arg[0] == "int":
            app_args.append(int(sub_arg[1]))
        elif sub_arg[0] == "addr":
            app_args.append(encoding.decode_address(sub_arg[1]))
    return app_args


@step(
    'I build a payment transaction with sender "{sender:MaybeString}", receiver "{receiver:MaybeString}", amount {amount}, close remainder to "{close_remainder_to:MaybeString}"'
)
def build_payment_transaction(
    context, sender, receiver, amount, close_remainder_to
):
    if sender == "transient":
        sender = context.transient_pk
    if receiver == "transient":
        receiver = context.transient_pk
    if not close_remainder_to:
        close_remainder_to = None
    context.transaction = transaction.PaymentTxn(
        sender=sender,
        sp=context.suggested_params,
        receiver=receiver,
        amt=int(amount),
        close_remainder_to=close_remainder_to,
    )


@when(
    'I build an application transaction with operation "{operation:MaybeString}", application-id {application_id}, sender "{sender:MaybeString}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, app-args "{app_args:MaybeString}", foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", fee {fee}, first-valid {first_valid}, last-valid {last_valid}, genesis-hash "{genesis_hash:MaybeString}", extra-pages {extra_pages}'
)
def build_app_transaction(
    context,
    operation,
    application_id,
    sender,
    approval_program,
    clear_program,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    app_args,
    foreign_apps,
    foreign_assets,
    app_accounts,
    fee,
    first_valid,
    last_valid,
    genesis_hash,
    extra_pages,
):
    if operation == "none":
        operation = None
    else:
        operation = operation_string_to_enum(operation)
    if sender == "none":
        sender = None
    if approval_program == "none":
        approval_program = None
    elif approval_program:
        approval_program = read_program(context, approval_program)
    if clear_program == "none":
        clear_program = None
    elif clear_program:
        clear_program = read_program(context, clear_program)
    if app_args == "none":
        app_args = None
    elif app_args:
        app_args = split_and_process_app_args(app_args)
    if foreign_apps == "none":
        foreign_apps = None
    elif foreign_apps:
        foreign_apps = [int(app) for app in foreign_apps.split(",")]
    if foreign_assets == "none":
        foreign_assets = None
    elif foreign_assets:
        foreign_assets = [int(app) for app in foreign_assets.split(",")]
    if app_accounts == "none":
        app_accounts = None
    elif app_accounts:
        app_accounts = [
            account_pubkey for account_pubkey in app_accounts.split(",")
        ]
    if genesis_hash == "none":
        genesis_hash = None
    local_schema = transaction.StateSchema(
        num_uints=int(local_ints), num_byte_slices=int(local_bytes)
    )
    global_schema = transaction.StateSchema(
        num_uints=int(global_ints), num_byte_slices=int(global_bytes)
    )
    sp = transaction.SuggestedParams(
        int(fee),
        int(first_valid),
        int(last_valid),
        genesis_hash,
        flat_fee=True,
    )
    context.transaction = transaction.ApplicationCallTxn(
        sender=sender,
        sp=sp,
        index=int(application_id),
        on_complete=operation,
        local_schema=local_schema,
        global_schema=global_schema,
        approval_program=approval_program,
        clear_program=clear_program,
        app_args=app_args,
        accounts=app_accounts,
        foreign_apps=foreign_apps,
        foreign_assets=foreign_assets,
        extra_pages=int(extra_pages),
        note=None,
        lease=None,
        rekey_to=None,
    )


@when("sign the transaction")
def sign_transaction_with_signing_account(context):
    private_key = mnemonic.to_private_key(context.signing_mnemonic)
    context.signed_transaction = context.transaction.sign(private_key)


@then('the base64 encoded signed transactions should equal "{goldens}"')
def compare_stxns_array_to_base64_golden(context, goldens):
    golden_strings = goldens.split(",")
    assert len(golden_strings) == len(context.signed_transactions)
    for i, golden in enumerate(golden_strings):
        actual_base64 = encoding.msgpack_encode(context.signed_transactions[i])
        assert golden == actual_base64, "actual is {}".format(actual_base64)


@then('the base64 encoded signed transaction should equal "{golden}"')
def compare_to_base64_golden(context, golden):
    actual_base64 = encoding.msgpack_encode(context.signed_transaction)
    assert golden == actual_base64, "actual is {}".format(actual_base64)


@then("the decoded transaction should equal the original")
def compare_to_original(context):
    encoded = encoding.msgpack_encode(context.signed_transaction)
    decoded = encoding.future_msgpack_decode(encoded)
    assert decoded.transaction == context.transaction


@given(
    'an algod v2 client connected to "{host}" port {port} with token "{token}"'
)
def algod_v2_client_at_host_port_and_token(context, host, port, token):
    algod_address = "http://" + str(host) + ":" + str(port)
    context.app_acl = algod.AlgodClient(token, algod_address)


@given("an algod v2 client")
def algod_v2_client(context):
    algod_address = "http://localhost" + ":" + str(algod_port)
    context.app_acl = algod.AlgodClient(daemon_token, algod_address)


@given(
    "I create a new transient account and fund it with {transient_fund_amount} microalgos."
)
def create_transient_and_fund(context, transient_fund_amount):
    context.transient_sk, context.transient_pk = account.generate_account()
    sp = context.app_acl.suggested_params()
    payment = transaction.PaymentTxn(
        context.accounts[0],
        sp,
        context.transient_pk,
        int(transient_fund_amount),
    )
    signed_payment = context.wallet.sign_transaction(payment)
    context.app_acl.send_transaction(signed_payment)
    transaction.wait_for_confirmation(context.app_acl, payment.get_txid(), 10)


@step(
    'I build an application transaction with the transient account, the current application, suggested params, operation "{operation}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, app-args "{app_args:MaybeString}", foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", extra-pages {extra_pages}'
)
def build_app_txn_with_transient(
    context,
    operation,
    approval_program,
    clear_program,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    app_args,
    foreign_apps,
    foreign_assets,
    app_accounts,
    extra_pages,
):
    application_id = 0
    if operation == "none":
        operation = None
    else:
        if (
            hasattr(context, "current_application_id")
            and context.current_application_id
            and operation != "create"
        ):
            application_id = context.current_application_id
        operation = operation_string_to_enum(operation)
    if approval_program == "none":
        approval_program = None
    elif approval_program:
        approval_program = read_program(context, approval_program)
    if clear_program == "none":
        clear_program = None
    elif clear_program:
        clear_program = read_program(context, clear_program)
    local_schema = transaction.StateSchema(
        num_uints=int(local_ints), num_byte_slices=int(local_bytes)
    )
    global_schema = transaction.StateSchema(
        num_uints=int(global_ints), num_byte_slices=int(global_bytes)
    )
    if app_args == "none":
        app_args = None
    elif app_args:
        app_args = split_and_process_app_args(app_args)
    if foreign_apps == "none":
        foreign_apps = None
    elif foreign_apps:
        foreign_apps = [int(app) for app in foreign_apps.split(",")]
    if foreign_assets == "none":
        foreign_assets = None
    elif foreign_assets:
        foreign_assets = [int(asset) for asset in foreign_assets.split(",")]
    if app_accounts == "none":
        app_accounts = None
    elif app_accounts:
        app_accounts = [
            account_pubkey for account_pubkey in app_accounts.split(",")
        ]

    sp = context.app_acl.suggested_params()
    context.app_transaction = transaction.ApplicationCallTxn(
        sender=context.transient_pk,
        sp=sp,
        index=int(application_id),
        on_complete=operation,
        local_schema=local_schema,
        global_schema=global_schema,
        approval_program=approval_program,
        clear_program=clear_program,
        app_args=app_args,
        accounts=app_accounts,
        foreign_apps=foreign_apps,
        foreign_assets=foreign_assets,
        extra_pages=int(extra_pages),
        note=None,
        lease=None,
        rekey_to=None,
    )


@step(
    'I sign and submit the transaction, saving the txid. If there is an error it is "{error_string:MaybeString}".'
)
def sign_submit_save_txid_with_error(context, error_string):
    try:
        signed_app_transaction = context.app_transaction.sign(
            context.transient_sk
        )
        context.app_txid = context.app_acl.send_transaction(
            signed_app_transaction
        )
    except Exception as e:
        if not error_string or error_string not in str(e):
            raise RuntimeError(
                "error string "
                + error_string
                + " not in actual error "
                + str(e)
            )


@step("I wait for the transaction to be confirmed.")
def wait_for_app_txn_confirm(context):
    sp = context.app_acl.suggested_params()
    last_round = sp.first
    context.app_acl.status_after_block(last_round + 2)
    if hasattr(context, "acl"):
        assert "type" in context.acl.transaction_info(
            context.transient_pk, context.app_txid
        )
        assert "type" in context.acl.transaction_by_id(context.app_txid)
    else:
        transaction.wait_for_confirmation(
            context.app_acl, context.app_txid, 10
        )


@given("I reset the array of application IDs to remember.")
def reset_appid_list(context):
    context.app_ids = []


@step("I remember the new application ID.")
def remember_app_id(context):
    if hasattr(context, "acl"):
        app_id = context.acl.pending_transaction_info(context.app_txid)[
            "txresults"
        ]["createdapp"]
    else:
        app_id = context.app_acl.pending_transaction_info(context.app_txid)[
            "application-index"
        ]

    context.current_application_id = app_id
    if not hasattr(context, "app_ids"):
        context.app_ids = []

    context.app_ids.append(app_id)


@then(
    "I get the account address for the current application and see that it matches the app id's hash"
)
def assert_app_account_is_the_hash(context):
    app_id = context.current_application_id
    expected = encoding.encode_address(
        encoding.checksum(b"appID" + app_id.to_bytes(8, "big"))
    )
    actual = logic.get_application_address(app_id)
    assert (
        expected == actual
    ), f"account-address: expected [{expected}], but got [{actual}]"


def fund_account_address(
    context, account_address: str, amount: Union[int, str]
):
    sp = context.app_acl.suggested_params()
    payment = transaction.PaymentTxn(
        context.accounts[0],
        sp,
        account_address,
        int(amount),
    )
    signed_payment = context.wallet.sign_transaction(payment)
    context.app_acl.send_transaction(signed_payment)
    transaction.wait_for_confirmation(context.app_acl, payment.get_txid(), 10)


@given(
    "I fund the current application's address with {fund_amount} microalgos."
)
def fund_app_account(context, fund_amount):
    fund_account_address(
        context,
        logic.get_application_address(context.current_application_id),
        fund_amount,
    )


@given("an application id {app_id}")
def set_app_id(context, app_id):
    context.current_application_id = app_id


@step(
    'The transient account should have the created app "{app_created_bool_as_string:MaybeString}" and total schema byte-slices {byte_slices} and uints {uints}, the application "{application_state:MaybeString}" state contains key "{state_key:MaybeString}" with value "{state_value:MaybeString}"'
)
def verify_app_txn(
    context,
    app_created_bool_as_string,
    byte_slices,
    uints,
    application_state,
    state_key,
    state_value,
):
    account_info = context.app_acl.account_info(context.transient_pk)
    app_total_schema = account_info["apps-total-schema"]
    assert app_total_schema["num-byte-slice"] == int(byte_slices)
    assert app_total_schema["num-uint"] == int(uints)

    app_created = app_created_bool_as_string == "true"
    created_apps = account_info["created-apps"]
    # If we don't expect the app to exist, verify that it isn't there and exit.
    if not app_created:
        for app in created_apps:
            assert app["id"] != context.current_application_id
        return

    found_app = False
    for app in created_apps:
        found_app = found_app or app["id"] == context.current_application_id
    assert found_app

    # If there is no key to check, we're done.
    if state_key is None or state_key == "":
        return

    found_value_for_key = False
    key_values = list()
    if application_state == "local":
        counter = 0
        for local_state in account_info["apps-local-state"]:
            if local_state["id"] == context.current_application_id:
                key_values = local_state["key-value"]
                counter = counter + 1
        assert counter == 1
    elif application_state == "global":
        counter = 0
        for created_app in account_info["created-apps"]:
            if created_app["id"] == context.current_application_id:
                key_values = created_app["params"]["global-state"]
                counter = counter + 1
        assert counter == 1
    else:
        raise NotImplementedError(
            'test does not understand application state "'
            + application_state
            + '"'
        )

    assert len(key_values) > 0

    for key_value in key_values:
        found_key = key_value["key"]
        if found_key == state_key:
            found_value_for_key = True
            found_value = key_value["value"]
            if found_value["type"] == 1:
                assert found_value["bytes"] == state_value
            elif found_value["type"] == 0:
                assert found_value["uint"] == int(state_value)
    assert found_value_for_key


def load_resource(res, is_binary=True):
    """load data from features/resources"""
    path = Path(__file__).parent.parent / "features" / "resources" / res
    filemode = "rb" if is_binary else "r"
    with open(path, filemode) as fin:
        data = fin.read()
    return data


def read_program_binary(path):
    return bytearray(load_resource(path))


def read_program(context, path):
    """
    Assumes that have already added `context.app_acl` so need to have previously
    called one of the steps beginning with "Given an algod v2 client..."
    """
    if path.endswith(".teal"):
        assert hasattr(
            context, "app_acl"
        ), "Cannot compile teal program into binary because no algod v2 client has been provided in the context"

        teal = load_resource(path, is_binary=False)
        resp = context.app_acl.compile(teal)
        return base64.b64decode(resp["result"])

    return read_program_binary(path)


@when('I compile a teal program "{program}"')
def compile_step(context, program):
    data = load_resource(program)
    source = data.decode("utf-8")

    try:
        context.response = context.app_acl.compile(source)
        context.status = 200
    except AlgodHTTPError as ex:
        context.status = ex.code
        context.response = dict(result="", hash="")


@then(
    'it is compiled with {status} and "{result:MaybeString}" and "{hash:MaybeString}"'
)
def compile_check_step(context, status, result, hash):
    assert context.status == int(status)
    assert context.response["result"] == result
    assert context.response["hash"] == hash


@then(
    'base64 decoding the response is the same as the binary "{binary:MaybeString}"'
)
def b64decode_compiled_teal_step(context, binary):
    binary = load_resource(binary)
    response_result = context.response["result"]
    assert base64.b64decode(response_result.encode()) == binary


@when('I dryrun a "{kind}" program "{program}"')
def dryrun_step(context, kind, program):
    data = load_resource(program)
    sp = transaction.SuggestedParams(
        int(1000), int(1), int(100), "", flat_fee=True
    )
    zero_addr = encoding.encode_address(bytes(32))
    txn = transaction.Transaction(zero_addr, sp, None, None, "pay", None)
    sources = []

    if kind == "compiled":
        lsig = transaction.LogicSig(data)
        txns = [transaction.LogicSigTransaction(txn, lsig)]
    elif kind == "source":
        txns = [transaction.SignedTransaction(txn, None)]
        sources = [DryrunSource(field_name="lsig", source=data, txn_index=0)]
    else:
        assert False, f"kind {kind} not in (source, compiled)"

    drr = DryrunRequest(txns=txns, sources=sources)
    context.response = context.app_acl.dryrun(drr)


@then('I get execution result "{result}"')
def dryrun_check_step(context, result):
    ddr = context.response
    assert len(ddr["txns"]) > 0

    res = ddr["txns"][0]
    if (
        res["logic-sig-messages"] is not None
        and len(res["logic-sig-messages"]) > 0
    ):
        msgs = res["logic-sig-messages"]
    elif (
        res["app-call-messages"] is not None
        and len(res["app-call-messages"]) > 0
    ):
        msgs = res["app-call-messages"]

    assert len(msgs) > 0
    assert msgs[-1] == result


@when("we make any Dryrun call")
def dryrun_any_call_step(context):
    context.response = context.acl.dryrun(DryrunRequest())


@then(
    'the parsed Dryrun Response should have global delta "{creator}" with {action}'
)
def dryrun_parsed_response(context, creator, action):
    ddr = context.response
    assert len(ddr["txns"]) > 0

    delta = ddr["txns"][0]["global-delta"]
    assert len(delta) > 0
    assert delta[0]["key"] == creator
    assert delta[0]["value"]["action"] == int(action)


@given('dryrun test case with "{program}" of type "{kind}"')
def dryrun_test_case_step(context, program, kind):
    if kind not in set(["lsig", "approv", "clearp"]):
        assert False, f"kind {kind} not in (lsig, approv, clearp)"

    prog = load_resource(program)
    # check if source
    if prog[0] > 0x20:
        prog = prog.decode("utf-8")

    context.dryrun_case_program = prog
    context.dryrun_case_kind = kind


@then('status assert of "{status}" is succeed')
def dryrun_test_case_status_assert_step(context, status):
    class TestCase(DryrunTestCaseMixin, unittest.TestCase):
        """Mock TestCase to test"""

    ts = TestCase()
    ts.algo_client = context.app_acl

    lsig = None
    app = None
    if context.dryrun_case_kind == "lsig":
        lsig = dict()
    if context.dryrun_case_kind == "approv":
        app = dict()
    elif context.dryrun_case_kind == "clearp":
        app = dict(on_complete=transaction.OnComplete.ClearStateOC)

    if status == "PASS":
        ts.assertPass(context.dryrun_case_program, lsig=lsig, app=app)
    else:
        ts.assertReject(context.dryrun_case_program, lsig=lsig, app=app)


def dryrun_test_case_global_state_assert_impl(
    context, key, value, action, raises
):
    class TestCase(DryrunTestCaseMixin, unittest.TestCase):
        """Mock TestCase to test"""

    ts = TestCase()
    ts.algo_client = context.app_acl

    action = int(action)

    val = dict(action=action)
    if action == 1:
        val["bytes"] = value
    elif action == 2:
        val["uint"] = int(value)

    on_complete = transaction.OnComplete.NoOpOC
    if context.dryrun_case_kind == "clearp":
        on_complete = transaction.OnComplete.ClearStateOC

    raised = False
    try:
        ts.assertGlobalStateContains(
            context.dryrun_case_program,
            dict(key=key, value=val),
            app=dict(on_complete=on_complete),
        )
    except AssertionError:
        raised = True

    if raises:
        ts.assertTrue(raised, "assertGlobalStateContains expected to raise")


@then('global delta assert with "{key}", "{value}" and {action} is succeed')
def dryrun_test_case_global_state_assert_step(context, key, value, action):
    dryrun_test_case_global_state_assert_impl(
        context, key, value, action, False
    )


@then('global delta assert with "{key}", "{value}" and {action} is failed')
def dryrun_test_case_global_state_assert_fail_step(
    context, key, value, action
):
    dryrun_test_case_global_state_assert_impl(
        context, key, value, action, True
    )


@then(
    'local delta assert for "{account}" of accounts {index} with "{key}", "{value}" and {action} is succeed'
)
def dryrun_test_case_local_state_assert_fail_step(
    context, account, index, key, value, action
):
    class TestCase(DryrunTestCaseMixin, unittest.TestCase):
        """Mock TestCase to test"""

    ts = TestCase()
    ts.algo_client = context.app_acl

    action = int(action)

    val = dict(action=action)
    if action == 1:
        val["bytes"] = value
    elif action == 2:
        val["uint"] = int(value)

    on_complete = transaction.OnComplete.NoOpOC
    if context.dryrun_case_kind == "clearp":
        on_complete = transaction.OnComplete.ClearStateOC

    app_idx = 1
    accounts = [
        Account(
            address=ts.default_address(),
            status="Offline",
            apps_local_state=[ApplicationLocalState(id=app_idx)],
        )
    ] * 2
    accounts[int(index)].address = account

    drr = ts.dryrun_request(
        context.dryrun_case_program,
        sender=accounts[0].address,
        app=dict(app_idx=app_idx, on_complete=on_complete, accounts=accounts),
    )

    ts.assertNoError(drr)
    ts.assertLocalStateContains(drr, account, dict(key=key, value=val))


@given("a new AtomicTransactionComposer")
def create_atomic_transaction_composer(context):
    context.atomic_transaction_composer = (
        atomic_transaction_composer.AtomicTransactionComposer()
    )
    context.method_list = []


@step("I make a transaction signer for the {account_type} account.")
def create_transaction_signer(context, account_type):
    if account_type == "transient":
        private_key = context.transient_sk
    elif account_type == "signing":
        private_key = mnemonic.to_private_key(context.signing_mnemonic)
    else:
        raise NotImplementedError(
            "cannot make transaction signer for " + account_type
        )
    context.transaction_signer = (
        atomic_transaction_composer.AccountTransactionSigner(private_key)
    )


@step('I create the Method object from method signature "{method_signature}"')
def build_abi_method(context, method_signature):
    context.abi_method = abi.Method.from_signature(method_signature)
    if not hasattr(context, "method_list"):
        context.method_list = []
    context.method_list.append(context.abi_method)


@step("I create a transaction with signer with the current transaction.")
def create_transaction_with_signer(context):
    context.transaction_with_signer = (
        atomic_transaction_composer.TransactionWithSigner(
            context.transaction, context.transaction_signer
        )
    )


@when("I add the current transaction with signer to the composer.")
def add_transaction_to_composer(context):
    context.atomic_transaction_composer.add_transaction(
        context.transaction_with_signer
    )


def process_abi_args(context, method, arg_tokens):
    method_args = []
    for arg_index, arg in enumerate(method.args):
        # Skip arg if it does not have a type
        if isinstance(arg.type, abi.ABIType):
            method_arg = arg.type.decode(
                base64.b64decode(arg_tokens[arg_index])
            )
            method_args.append(method_arg)
        elif arg.type == abi.ABIReferenceType.ACCOUNT:
            method_arg = abi.AddressType().decode(
                base64.b64decode(arg_tokens[arg_index])
            )
            method_args.append(method_arg)
        elif (
            arg.type == abi.ABIReferenceType.APPLICATION
            or arg.type == abi.ABIReferenceType.ASSET
        ):
            parts = arg_tokens[arg_index].split(":")
            if len(parts) == 2 and parts[0] == "ctxAppIdx":
                method_arg = context.app_ids[int(parts[1])]
            else:
                method_arg = abi.UintType(64).decode(
                    base64.b64decode(arg_tokens[arg_index])
                )
            method_args.append(method_arg)
        else:
            # Append the transaction signer as is
            method_args.append(arg_tokens[arg_index])
    return method_args


@step("I create a new method arguments array.")
def create_abi_method_args(context):
    context.method_args = []


@step(
    "I append the current transaction with signer to the method arguments array."
)
def append_txn_to_method_args(context):
    context.method_args.append(context.transaction_with_signer)


@step(
    'I append the encoded arguments "{method_args:MaybeString}" to the method arguments array.'
)
def append_app_args_to_method_args(context, method_args):
    # Returns a list of ABI method arguments
    app_args = method_args.split(",")
    context.method_args += app_args


@given('I add the nonce "{nonce}"')
def add_nonce(context, nonce):
    context.nonce = nonce


def abi_method_adder(
    context,
    account_type,
    operation,
    create_when_calling=False,
    approval_program_path=None,
    clear_program_path=None,
    global_bytes=None,
    global_ints=None,
    local_bytes=None,
    local_ints=None,
    extra_pages=None,
    force_unique_transactions=False,
):
    if account_type == "transient":
        sender = context.transient_pk
    elif account_type == "signing":
        sender = mnemonic.to_public_key(context.signing_mnemonic)
    else:
        raise NotImplementedError(
            "cannot make transaction signer for " + account_type
        )
    approval_program = clear_program = None
    global_schema = local_schema = None

    def int_if_given(given):
        return int(given) if given else 0

    local_schema = global_schema = None
    if create_when_calling:
        if approval_program_path:
            approval_program = read_program(context, approval_program_path)
        if clear_program_path:
            clear_program = read_program(context, clear_program_path)
        if local_ints or local_bytes:
            local_schema = transaction.StateSchema(
                num_uints=int_if_given(local_ints),
                num_byte_slices=int_if_given(local_bytes),
            )
        if global_ints or global_bytes:
            global_schema = transaction.StateSchema(
                num_uints=int_if_given(global_ints),
                num_byte_slices=int_if_given(global_bytes),
            )
        extra_pages = int_if_given(extra_pages)

    app_id = int(context.current_application_id)

    app_args = process_abi_args(
        context, context.abi_method, context.method_args
    )
    note = None
    if force_unique_transactions:
        note = (
            b"I should be unique thanks to this nonce: "
            + context.nonce.encode()
        )

    context.atomic_transaction_composer.add_method_call(
        app_id=app_id,
        method=context.abi_method,
        sender=sender,
        sp=context.suggested_params,
        signer=context.transaction_signer,
        method_args=app_args,
        on_complete=operation_string_to_enum(operation),
        local_schema=local_schema,
        global_schema=global_schema,
        approval_program=approval_program,
        clear_program=clear_program,
        extra_pages=extra_pages,
        note=note,
    )


@step(
    'I add a nonced method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments.'
)
def add_abi_method_call_nonced(context, account_type, operation):
    abi_method_adder(
        context,
        account_type,
        operation,
        force_unique_transactions=True,
    )


@step(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments.'
)
def add_abi_method_call(context, account_type, operation):
    abi_method_adder(
        context,
        account_type,
        operation,
    )


@when(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments, approval-program "{approval_program_path:MaybeString}", clear-program "{clear_program_path:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, extra-pages {extra_pages}.'
)
def add_abi_method_call_creation_with_allocs(
    context,
    account_type,
    operation,
    approval_program_path,
    clear_program_path,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    extra_pages,
):
    abi_method_adder(
        context,
        account_type,
        operation,
        True,
        approval_program_path,
        clear_program_path,
        global_bytes,
        global_ints,
        local_bytes,
        local_ints,
        extra_pages,
    )


@when(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments, approval-program "{approval_program_path:MaybeString}", clear-program "{clear_program_path:MaybeString}".'
)
def add_abi_method_call_creation(
    context,
    account_type,
    operation,
    approval_program_path,
    clear_program_path,
):
    abi_method_adder(
        context,
        account_type,
        operation,
        True,
        approval_program_path,
        clear_program_path,
    )


@step(
    'I build the transaction group with the composer. If there is an error it is "{error_string:MaybeString}".'
)
def build_atomic_transaction_group(context, error_string):
    try:
        context.atomic_transaction_composer.build_group()
    except Exception as e:
        if not error_string:
            raise RuntimeError(f"Unexpected error for building composer {e}")
        elif error_string == "zero group size error":
            error_message = (
                "no transactions to build for AtomicTransactionComposer"
            )
            assert error_message in str(e)
        else:
            raise NotImplemented(
                f"Unknown error string for building composer: {error_string}"
            )


def composer_status_string_to_enum(status):
    if status == "BUILDING":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.BUILDING
        )
    elif status == "BUILT":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.BUILT
        )
    elif status == "SIGNED":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.SIGNED
        )
    elif status == "SUBMITTED":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.SUBMITTED
        )
    elif status == "COMMITTED":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.COMMITTED
        )
    else:
        raise NotImplementedError(
            "no AtomicTransactionComposerStatus enum for " + status
        )


@then('The composer should have a status of "{status}".')
def check_atomic_transaction_composer_status(context, status):
    assert (
        context.atomic_transaction_composer.get_status()
        == composer_status_string_to_enum(status)
    )


@then("I gather signatures with the composer.")
def gather_signatures_composer(context):
    context.signed_transactions = (
        context.atomic_transaction_composer.gather_signatures()
    )


@then("I clone the composer.")
def clone_atomic_transaction_composer(context):
    context.atomic_transaction_composer = (
        context.atomic_transaction_composer.clone()
    )


@then("I execute the current transaction group with the composer.")
def execute_atomic_transaction_composer(context):
    context.atomic_transaction_composer_return = (
        context.atomic_transaction_composer.execute(context.app_acl, 10)
    )
    assert context.atomic_transaction_composer_return.confirmed_round > 0


@then('The app should have returned "{returns:MaybeString}".')
def check_atomic_transaction_composer_response(context, returns):
    if not returns:
        expected_tokens = []
        assert len(context.atomic_transaction_composer_return.abi_results) == 1
        result = context.atomic_transaction_composer_return.abi_results[0]
        assert result.return_value is None
        assert result.decode_error is None
    else:
        expected_tokens = returns.split(",")
        for i, expected in enumerate(expected_tokens):
            result = context.atomic_transaction_composer_return.abi_results[i]
            if not returns or not expected_tokens[i]:
                assert result.return_value is None
                assert result.decode_error is None
                continue
            expected_bytes = base64.b64decode(expected)
            expected_value = context.method_list[i].returns.type.decode(
                expected_bytes
            )

            assert expected_bytes == result.raw_value, "actual is {}".format(
                result.raw_value
            )
            assert (
                expected_value == result.return_value
            ), "actual is {}".format(result.return_value)
            assert result.decode_error is None


@then('The app should have returned ABI types "{abiTypes:MaybeString}".')
def check_atomic_transaction_composer_return_type(context, abiTypes):
    expected_tokens = abiTypes.split(":")
    results = context.atomic_transaction_composer_return.abi_results
    assert len(expected_tokens) == len(
        results
    ), f"surprisingly, we don't have the same number of expected results ({len(expected_tokens)}) as actual results ({len(results)})"
    for i, expected in enumerate(expected_tokens):
        result = results[i]
        assert result.decode_error is None

        if expected == "void":
            assert result.raw_value is None
            with pytest.raises(ABITypeError):
                abi.ABIType.from_string(expected)
            continue

        expected_type = abi.ABIType.from_string(expected)
        decoded_result = expected_type.decode(result.raw_value)
        result_round_trip = expected_type.encode(decoded_result)
        assert result_round_trip == result.raw_value


@when("I serialize the Method object into json")
def serialize_method_to_json(context):
    context.json_output = context.abi_method.dictify()


@then(
    'the produced json should equal "{json_path}" loaded from "{json_directory}"'
)
def check_json_output_equals(context, json_path, json_directory):
    with open(
        "test/features/unit/" + json_directory + "/" + json_path, "rb"
    ) as f:
        loaded_response = json.load(f)
    assert context.json_output == loaded_response


@when(
    'I create the Method object with name "{method_name}" method description "{method_desc}" first argument type "{first_arg_type}" first argument description "{first_arg_desc}" second argument type "{second_arg_type}" second argument description "{second_arg_desc}" and return type "{return_arg_type}"'
)
def create_method_from_test_with_arg_name(
    context,
    method_name,
    method_desc,
    first_arg_type,
    first_arg_desc,
    second_arg_type,
    second_arg_desc,
    return_arg_type,
):
    context.abi_method = abi.Method(
        name=method_name,
        args=[
            abi.Argument(arg_type=first_arg_type, desc=first_arg_desc),
            abi.Argument(arg_type=second_arg_type, desc=second_arg_desc),
        ],
        returns=abi.Returns(return_arg_type),
        desc=method_desc,
    )


@when(
    'I create the Method object with name "{method_name}" first argument name "{first_arg_name}" first argument type "{first_arg_type}" second argument name "{second_arg_name}" second argument type "{second_arg_type}" and return type "{return_arg_type}"'
)
def create_method_from_test_with_arg_name(
    context,
    method_name,
    first_arg_name,
    first_arg_type,
    second_arg_name,
    second_arg_type,
    return_arg_type,
):
    context.abi_method = abi.Method(
        name=method_name,
        args=[
            abi.Argument(arg_type=first_arg_type, name=first_arg_name),
            abi.Argument(arg_type=second_arg_type, name=second_arg_name),
        ],
        returns=abi.Returns(return_arg_type),
    )


@when(
    'I create the Method object with name "{method_name}" first argument type "{first_arg_type}" second argument type "{second_arg_type}" and return type "{return_arg_type}"'
)
def create_method_from_test(
    context, method_name, first_arg_type, second_arg_type, return_arg_type
):
    context.abi_method = abi.Method(
        name=method_name,
        args=[abi.Argument(first_arg_type), abi.Argument(second_arg_type)],
        returns=abi.Returns(return_arg_type),
    )


@then("the deserialized json should equal the original Method object")
def deserialize_method_to_object(context):
    json_string = json.dumps(context.json_output)
    actual = abi.Method.from_json(json_string)
    assert actual == context.abi_method


@then("the txn count should be {txn_count}")
def check_method_txn_count(context, txn_count):
    assert context.abi_method.get_txn_calls() == int(txn_count)


@then('the method selector should be "{method_selector}"')
def check_method_selector(context, method_selector):
    assert context.abi_method.get_selector() == bytes.fromhex(method_selector)


@when(
    'I create an Interface object from the Method object with name "{interface_name}" and description "{description}"'
)
def create_interface_object(context, interface_name, description):
    context.abi_interface = abi.Interface(
        name=interface_name, desc=description, methods=[context.abi_method]
    )


@when("I serialize the Interface object into json")
def serialize_interface_to_json(context):
    context.json_output = context.abi_interface.dictify()


@then("the deserialized json should equal the original Interface object")
def deserialize_json_to_interface(context):
    actual = abi.Interface.undictify(context.json_output)
    assert actual == context.abi_interface


@when(
    'I create a Contract object from the Method object with name "{contract_name}" and description "{description}"'
)
def create_contract_object(context, contract_name, description):
    context.abi_contract = abi.Contract(
        name=contract_name, desc=description, methods=[context.abi_method]
    )


@when('I set the Contract\'s appID to {app_id} for the network "{network_id}"')
def set_contract_networks(context, app_id, network_id):
    if not context.abi_contract.networks:
        context.abi_contract.networks = {}
    context.abi_contract.networks[network_id] = NetworkInfo(int(app_id))


@when("I serialize the Contract object into json")
def serialize_contract_to_json(context):
    context.json_output = context.abi_contract.dictify()


@then("the deserialized json should equal the original Contract object")
def deserialize_json_to_contract(context):
    actual = abi.Contract.undictify(context.json_output)
    assert actual == context.abi_contract


@given(
    'a dryrun response file "{dryrun_response_file}" and a transaction at index "{txn_id}"'
)
def parse_dryrun_response_object(context, dryrun_response_file, txn_id):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    with open(
        dir_path + "/test/features/resources/" + dryrun_response_file, "r"
    ) as f:
        drr_dict = json.loads(f.read())

    context.dryrun_response_object = dryrun_results.DryrunResponse(drr_dict)
    context.dryrun_txn_result = context.dryrun_response_object.txns[
        int(txn_id)
    ]


@then('calling app trace produces "{app_trace_file}"')
def dryrun_compare_golden(context, app_trace_file):
    trace_expected = load_resource(app_trace_file, is_binary=False)

    dryrun_trace = context.dryrun_txn_result.app_trace()

    got_lines = dryrun_trace.split("\n")
    expected_lines = trace_expected.split("\n")

    print("{} {}".format(len(got_lines), len(expected_lines)))
    for idx in range(len(got_lines)):
        if got_lines[idx] != expected_lines[idx]:
            print(
                "  {}  \n{}\n{}\n".format(
                    idx, got_lines[idx], expected_lines[idx]
                )
            )

    assert trace_expected == dryrun_trace, "Expected \n{}\ngot\n{}\n".format(
        trace_expected, dryrun_trace
    )


@then(
    'I dig into the paths "{paths}" of the resulting atomic transaction tree I see group ids and they are all the same'
)
def same_groupids_for_paths(context, paths):
    paths = [[int(p) for p in path.split(",")] for path in paths.split(":")]
    grp = None
    for path in paths:
        d = context.atomic_transaction_composer_return.abi_results
        for idx, p in enumerate(path):
            d = d["inner-txns"][p] if idx else d[idx].tx_info
            _grp = d["txn"]["txn"]["grp"]
        if not grp:
            grp = _grp
        else:
            assert grp == _grp, f"non-constant txn group hashes {_grp} v {grp}"


@then(
    'I can dig the {i}th atomic result with path "{path}" and see the value "{field}"'
)
def glom_app_eval_delta(context, i, path, field):
    results = context.atomic_transaction_composer_return.abi_results
    actual_field = glom(results[int(i)].tx_info, path)
    assert field == str(
        actual_field
    ), f"path [{path}] expected value [{field}] but got [{actual_field}] instead"


def s512_256_uint64(witness):
    return int.from_bytes(encoding.checksum(witness)[:8], "big")


@then(
    "The {result_index}th atomic result for randomInt({input}) proves correct"
)
def sha512_256_of_witness_mod_n_is_result(context, result_index, input):
    input = int(input)
    abi_type = abi.ABIType.from_string("(uint64,byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    rand_int, witness = abi_type.decode(result.raw_value)
    witness = bytes(witness)
    x = s512_256_uint64(witness)
    quotient = x % input
    assert quotient == rand_int


@then(
    'The {result_index}th atomic result for randElement("{input}") proves correct'
)
def char_with_idx_sha512_256_of_witness_mod_n_is_result(
    context, result_index, input
):
    abi_type = abi.ABIType.from_string("(byte,byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    rand_elt, witness = abi_type.decode(result.raw_value)
    witness = bytes(witness)
    x = s512_256_uint64(witness)
    quotient = x % len(input)
    assert input[quotient] == bytes([rand_elt]).decode()


@then(
    'The {result_index}th atomic result for "spin()" satisfies the regex "{regex}"'
)
def spin_results_satisfy(context, result_index, regex):
    abi_type = abi.ABIType.from_string("(byte[3],byte[17],byte[17],byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    spin, _, _, _ = abi_type.decode(result.raw_value)
    spin = bytes(spin).decode()

    assert re.search(regex, spin), f"{spin} did not match the regex {regex}"
