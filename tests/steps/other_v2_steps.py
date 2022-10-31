import base64
import json
import os
import unittest
import urllib
from pathlib import Path
from urllib.request import Request, urlopen

import parse
from algosdk import dryrun_results, encoding, error, mnemonic, source_map
from algosdk.error import AlgodHTTPError
from algosdk.future import transaction
from algosdk.testing.dryrun import DryrunTestCaseMixin
from algosdk.v2client import *
from algosdk.v2client.models import (
    Account,
    ApplicationLocalState,
    DryrunRequest,
    DryrunSource,
)
from behave import (
    given,
    register_type,  # pylint: disable=no-name-in-module
    step,
    then,
    when,
)
from glom import glom
from tests.steps.steps import algod_port, indexer_port
from tests.steps.steps import token as daemon_token


@parse.with_pattern(r".*")
def parse_string(text):
    return text


register_type(MaybeString=parse_string)


@parse.with_pattern(r"true|false|")
def parse_bool(value):
    if value not in ("true", "false", ""):
        raise ValueError("Unknown value for include_all: {}".format(value))
    return value == "true"


register_type(MaybeBool=parse_bool)


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
def mock_http_responses(context, filename, directory, status):
    context.expected_status_code = int(status)
    with open("tests/features/resources/mock_response_status", "w") as f:
        f.write(status)
    mock_response(context, filename, directory)
    f = open("tests/features/resources/mock_response_path", "r")
    mock_response_path = f.read()
    f.close()
    f = open("tests/features/resources/" + mock_response_path, "r")
    expected_mock_response = f.read()
    f.close()
    expected_mock_response = bytes(expected_mock_response, "ascii")
    context.expected_mock_response = json.loads(expected_mock_response)


@when('we make any "{client}" call to "{endpoint}".')
def client_call(context, client, endpoint):
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
def parsed_equal_mock(context):
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


@when("we make a GetAssetByID call for assetID {asset_id}")
def asset_info(context, asset_id):
    context.response = context.acl.asset_info(int(asset_id))


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
def asset_txns2(
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
def txns_by_addr2(
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


@when(
    'we make a Lookup Block call against round {block:d} and header "{headerOnly:MaybeBool}"'
)
def lookup_block(context, block, headerOnly):
    print("Header only = " + str(headerOnly))
    context.response = context.icl.block_info(
        block=block, header_only=headerOnly
    )


@when("we make a Lookup Block call against round {block:d}")
def lookup_block(context, block):
    context.response = context.icl.block_info(block)


@when("we make any LookupBlock call")
def lookup_block_any(context):
    context.response = context.icl.block_info(12)


@then(
    'the parsed LookupBlock response should have previous block hash "{prevHash}"'
)
def parse_lookup_block(context, prevHash):
    assert context.response["previous-block-hash"] == prevHash


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
def search_txns2(
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
def parsed_search_for_txns(context, roundNum, length, index, rekeyTo):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert (
            context.response["transactions"][int(index)]["rekey-to"] == rekeyTo
        )


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


@then('expect error string to contain "{err:MaybeString}"')
def expect_error(context, err):
    # TODO: this should actually do the claimed action
    pass


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
def build_keyreg_txn(
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


@given("an indexer v2 client")
def indexer_v2_client(context):
    indexer_address = "http://localhost" + ":" + str(indexer_port)
    context.app_icl = indexer.IndexerClient("", indexer_address)


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


@then(
    'the produced json should equal "{json_path}" loaded from "{json_directory}"'
)
def check_json_output_equals(context, json_path, json_directory):
    with open(
        "tests/features/unit/" + json_directory + "/" + json_path, "rb"
    ) as f:
        loaded_response = json.load(f)
    assert context.json_output == loaded_response


@given(
    'a dryrun response file "{dryrun_response_file}" and a transaction at index "{txn_id}"'
)
def parse_dryrun_response_object(context, dryrun_response_file, txn_id):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    with open(
        dir_path + "/tests/features/resources/" + dryrun_response_file, "r"
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


@given('a source map json file "{sourcemap_file}"')
def parse_source_map(context, sourcemap_file):
    jsmap = json.loads(load_resource(sourcemap_file, is_binary=False))
    context.source_map = source_map.SourceMap(jsmap)


@then('the string composed of pc:line number equals "{pc_to_line}"')
def check_source_map(context, pc_to_line):
    buff = [
        f"{pc}:{line}" for pc, line in context.source_map.pc_to_line.items()
    ]
    actual = ";".join(buff)
    assert actual == pc_to_line, f"expected {pc_to_line} got {actual}"


@then('getting the line associated with a pc "{pc}" equals "{line}"')
def check_pc_to_line(context, pc, line):

    actual_line = context.source_map.get_line_for_pc(int(pc))
    assert actual_line == int(line), f"expected line {line} got {actual_line}"


@then('getting the last pc associated with a line "{line}" equals "{pc}"')
def check_line_to_pc(context, line, pc):
    actual_pcs = context.source_map.get_pcs_for_line(int(line))
    assert actual_pcs[-1] == int(pc), f"expected pc {pc} got {actual_pcs[-1]}"


@when('I compile a teal program "{teal}" with mapping enabled')
def check_compile_mapping(context, teal):
    data = load_resource(teal)
    source = data.decode("utf-8")
    response = context.app_acl.compile(source, source_map=True)
    context.raw_source_map = json.dumps(
        response["sourcemap"], separators=(",", ":")
    )


@then('the resulting source map is the same as the json "{sourcemap}"')
def check_mapping_equal(context, sourcemap):
    expected = load_resource(sourcemap).decode("utf-8").strip()
    nl = "\n"
    assert (
        context.raw_source_map == expected
    ), f"context.raw_source_map={nl}{context.raw_source_map}{nl}expected={nl}{expected}"


@when("we make a GetLightBlockHeaderProof call for round {round}")
def lightblock(context, round):
    context.response = context.acl.lightblockheader_proof(round)


@when("we make a GetStateProof call for round {round}")
def state_proofs(context, round):
    context.response = context.acl.stateproofs(round)


@when(
    'we make a GetTransactionProof call for round {round} txid "{txid}" and hashtype "{hashtype:MaybeString}"'
)
def transaction_proof(context, round, txid, hashtype):
    context.response = context.acl.transaction_proof(
        round, txid, hashtype, "msgpack"
    )


@when("we make a Lookup Block Hash call against round {round}")
def get_block_hash(context, round):
    context.response = context.acl.get_block_hash(round)
