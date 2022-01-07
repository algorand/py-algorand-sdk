import base64
import json
from datetime import datetime
from urllib.request import Request, urlopen

from behave import (
    given,
    when,
    then,
    step,
)

from algosdk import account, encoding, error, mnemonic
from algosdk.future import transaction
from algosdk.v2client import algod, indexer

from steps import token as daemon_token
from steps import algod_port
from step_utils import fund_account_address


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


# TODO: make this actually expect an error
@then('expect error string to contain "{err:MaybeString}"')
def expect_error(context, err):
    pass


@then(
    "the parsed Suggested Transaction Parameters response should have first round valid of {roundNum}"
)
def parse_suggested(context, roundNum):
    assert context.response.first == int(roundNum)


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


@when("we make any Suggested Transaction Parameters call")
def suggested_any(context):
    context.response = context.acl.suggested_params()


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


@when("we make any Pending Transaction Information call with json format")
def pending_txn_any2(context):
    context.response = context.acl.pending_transaction_info(
        "sdfsf", response_format="json"
    )
    x = 42


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


@then(
    'There are {numaccounts} with the asset, the first is "{account}" has "{isfrozen}" and {amount}'
)
def check_asset_balance(context, numaccounts, account, isfrozen, amount):
    assert len(context.response["balances"]) == int(numaccounts)
    assert context.response["balances"][0]["address"] == account
    assert context.response["balances"][0]["amount"] == int(amount)
    assert context.response["balances"][0]["is-frozen"] == (isfrozen == "true")


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


@then(
    'the parsed LookupAssetTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"'
)
def parse_asset_tns(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    assert context.response["transactions"][int(idx)]["sender"] == sender


@then(
    'the parsed LookupAccountTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"'
)
def parse_txns_by_addr(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(idx)]["sender"] == sender


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


@then('the parsed LookupAccountByID response should have address "{address}"')
def parse_account(context, address):
    assert context.response["account"]["address"] == address


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


@given(
    "I create a new transient account and fund it with {transient_fund_amount} microalgos."
)
def create_transient_and_fund(context, transient_fund_amount):
    context.transient_sk, context.transient_pk = account.generate_account()
    fund_account_address(context, context.transient_pk, transient_fund_amount)
