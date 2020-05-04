import threading
from behave import given, when, then
import base64
from algosdk import kmd
from algosdk.future import transaction
from algosdk import encoding
from algosdk.v2client import *
from algosdk import account
from algosdk import mnemonic
from algosdk import wallet
from algosdk import auction
from algosdk import util
from algosdk import constants
from algosdk.future import template
import os
from datetime import datetime
import hashlib
import json
import http.server
import socketserver
import json
import random
import time
import urllib
from urllib.request import Request, urlopen
import msgpack



class PathsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        m = json.dumps({"path": self.path})
        m = bytes(m, "ascii")
        self.wfile.write(m)

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        m = json.dumps({"path": self.path})
        m = bytes(m, "ascii")
        self.wfile.write(m)

class JsonHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if "mock" in self.path:
            f = open("test/features/unit/mock_response_path", "w")
            f.write(self.path[6:])
            f.close()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes("done", "ascii"))
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            f = open("test/features/unit/mock_response_path", "r")
            mock_response_path = f.read()
            f.close()
            f = open("test/features/unit/" + mock_response_path, "r")
            s = f.read()
            f.close()
            s = bytes(s, "ascii")
            self.wfile.write(s)

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        f = open("test/features/unit/mock_response_path", "r")
        mock_response_path = f.read()
        f.close()
        f = open("test/features/unit/" + mock_response_path, "r")
        s = f.read()
        f.close()
        s = bytes(s, "ascii")
        self.wfile.write(s)

@given("mock server recording request paths")
def setup_mockserver(context):
    port = random.randint(10001, 20000)
    context.url = "http://127.0.0.1:" + str(port)
    context.acl = algod.AlgodClient("algod_token", context.url)
    context.icl = indexer.IndexerClient("indexer_token", context.url)
    context.server = socketserver.TCPServer(("", port), PathsHandler)
    context.thread = threading.Thread(target=context.server.serve_forever)
    context.thread.start()
    time.sleep(1)

@given('mock http responses in "{jsonfiles}" loaded from "{directory}"')
def mock_response(context, jsonfiles, directory):
    port = random.randint(10001, 20000)
    context.url = "http://127.0.0.1:" + str(port)
    context.acl = algod.AlgodClient("algod_token", context.url)
    context.icl = indexer.IndexerClient("indexer_token", context.url)
    context.server = socketserver.TCPServer(("", port), JsonHandler)
    context.thread = threading.Thread(target=context.server.serve_forever)
    context.thread.start()
    time.sleep(1)
    req = Request(context.url+"/mock/"+directory + "/" +jsonfiles, method="GET")
    urlopen(req)

@when("we make a Shutdown call with timeout {timeout}")
def shutdown(context, timeout):
    context.response = context.acl.shutdown(int(timeout))

@when('we make any Shutdown call')
def shutdown_any(context):
    context.response = context.acl.shutdown(3)

@when('we make any Register Participation Keys call')
def reg_key_any(context):
    context.response = context.acl.register_participation_keys()


@when('we make a Register Participation Keys call against account "{account}" fee {fee} dilution {dilution} lastvalidround {lastvalid} and nowait "{nowait}"')
def reg_part_key(context, account, fee, dilution, lastvalid, nowait):
    context.response = context.acl.register_participation_keys(address=account, fee=int(fee), key_dilution=int(dilution),
        last_valid_round=int(lastvalid), no_wait=nowait=="true")

@when('we make a Pending Transaction Information against txid "{txid}" with format "{response_format}"')
def pending_txn_info(context, txid, response_format):
    context.response = context.acl.pending_transaction_info(txid, response_format=response_format)

@when('we make a Pending Transaction Information with max {max} and format "{response_format}"')
def pending_txn_with_max(context, max, response_format):
    context.response = context.acl.pending_transaction_info(int(max), response_format=response_format)

@when('we make any Pending Transactions Information call')
def pending_txn_any(context):
    context.response = context.acl.pending_transactions(100, response_format="msgpack")

@when('we make any Pending Transaction Information call')
def pending_txn_any2(context):
    context.response = context.acl.pending_transaction_info("sdfsf", response_format="msgpack")

@then('the parsed Pending Transaction Information response should have sender "{sender}"')
def parse_pending_txn(context, sender):
    assert context.response["txn"].transaction.sender == sender

@then('the parsed Pending Transactions Information response should contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_pending_txns(context, length, idx, sender):
    assert len(context.response["top-transactions"]) == int(length)
    assert context.response["top-transactions"][int(idx)].transaction.sender == sender

@when('we make a Pending Transactions By Address call against account "{account}" and max {max} and format "{response_format}"')
def pending_txns_by_addr(context, account, max, response_format):
    context.response = context.acl.pending_transactions_by_address(account, limit=int(max), response_format=response_format)

@when('we make any Pending Transactions By Address call')
def pending_txns_by_addr_any(context):
    context.response = context.acl.pending_transactions_by_address("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI", response_format="msgpack")

@then('the parsed Pending Transactions By Address response should contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_pend_by_addr(context, length, idx, sender):
    assert len(context.response["top-transactions"]) == int(length)
    assert context.response["top-transactions"][int(idx)].transaction.sender == sender

@when('we make any Send Raw Transaction call')
def send_any(context):
    context.response = context.acl.send_raw_transaction("Bg==")

@then('the parsed Send Raw Transaction response should have txid "{txid}"')
def parsed_send(context, txid):
    assert context.response == txid

@when('we make any Node Status call')
def status_any(context):
    context.response = context.acl.status()

@then('the parsed Node Status response should have a last round of {roundNum}')
def parse_status(context, roundNum):
    assert context.response["last-round"] == int(roundNum)

@when('we make a Status after Block call with round {block}')
def status_after(context, block):
    context.response = context.acl.status_after_block(int(block))

@when('we make any Status After Block call')
def status_after_any(context):
    context.response = context.acl.status_after_block(3)

@then('the parsed Status After Block response should have a last round of {roundNum}')
def parse_status_after(context, roundNum):
    assert context.response["last-round"] == int(roundNum)

@when('we make any Ledger Supply call')
def ledger_any(context):
    context.response = context.acl.ledger_supply()

@then('the parsed Ledger Supply response should have totalMoney {tot} onlineMoney {online} on round {roundNum}')
def parse_ledger(context, tot, online, roundNum):
    assert context.response["online-money"] == int(online)
    assert context.response["total-money"] == int(tot)
    assert context.response["current_round"] == int(roundNum)

@when('we make an Account Information call against account "{account}"')
def acc_info(context, account):
    context.response = context.acl.account_info(account)

@when('we make any Account Information call')
def acc_info_any(context):
    context.response = context.acl.account_info("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI")

@then('the parsed Account Information response should have address "{address}"')
def parse_acc_info(context, address):
    assert context.response["address"] == address

@when('we make a Get Block call against block number {block} with format "{response_format}"')
def block(context, block, response_format):
    context.response = context.acl.block_info(int(block), response_format=response_format)

@when('we make any Get Block call')
def block_any(context):
    context.response = context.acl.block_info(3, response_format="msgpack")

@then('the parsed Get Block response should have rewards pool "{pool}"')
def parse_block(context, pool):
    print(pool)
    print(base64.b64decode(pool))
    print(base64.b64decode(context.response["block"]["rwd"]))
    print(context.response["block"]["rwd"])
    print(base64.b64encode(context.response["block"]["rwd"]).decode())
    assert base64.b64encode(context.response["block"]["rwd"]).decode() == pool

@when('we make a Lookup Asset Balances call against asset index {index} with limit {limit} afterAddress "{afterAddress}" round {block} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan}')
def asset_balance(context, index, limit, afterAddress, block, currencyGreaterThan, currencyLessThan):
    context.response = context.icl.asset_balances(int(index), int(limit), next_page=None, min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan), block=int(block))

@when('we make any LookupAssetBalances call')
def asset_balance_any(context):
    context.response = context.icl.asset_balances(123, 10)

@then('the parsed LookupAssetBalances response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have address "{address}" amount {amount} and frozen state "{frozenState}"')
def parse_asset_balance(context, roundNum, length, idx, address, amount, frozenState):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["balances"]) == int(length)
    assert context.response["balances"][int(idx)]["address"] == address
    assert context.response["balances"][int(idx)]["amount"] == int(amount)
    assert context.response["balances"][int(idx)]["is-frozen"] == (frozenState == "true")

@when('we make a Lookup Asset Transactions call against asset index {index} with NotePrefix "{notePrefixB64}" TxType "{txType}" SigType "{sigType}" txid "{txid}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime}" afterTime "{afterTime}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} address "{address}" addressRole "{addressRole}" ExcluseCloseTo "{excludeCloseTo}"')
def asset_txns(context, index, notePrefixB64, txType, sigType, txid, block, minRound, maxRound, limit, beforeTime, afterTime, currencyGreaterThan, currencyLessThan, address, addressRole, excludeCloseTo):
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
    context.response = context.icl.search_asset_transactions(int(index), limit=int(limit), next_page=None, note_prefix=base64.b64decode(notePrefixB64), txn_type=txType,
        sig_type=sigType, txid=txid, block=int(block), min_round=int(minRound), max_round=int(maxRound),
        start_time=afterTime, end_time=beforeTime, min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan), address=address, address_role=addressRole,
        exclude_close_to=excludeCloseTo=="true")

@when('we make any LookupAssetTransactions call')
def asset_txns_any(context):
    context.response = context.icl.search_asset_transactions(32)

@then('the parsed LookupAssetTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_asset_tns(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    assert context.response["transactions"][int(idx)]["sender"] == sender
    
@when('we make a Lookup Account Transactions call against account "{account}" with NotePrefix "{notePrefixB64}" TxType "{txType}" SigType "{sigType}" txid "{txid}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime}" afterTime "{afterTime}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index} addressRole "{addressRole}" ExcluseCloseTo "{excludeCloseTo}"')
def txns_by_addr(context, account, notePrefixB64, txType, sigType, txid, block, minRound, maxRound, limit, beforeTime, afterTime, currencyGreaterThan, currencyLessThan, index, addressRole, excludeCloseTo):
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
    if addressRole == "none":
        addressRole = None
    context.response = context.icl.search_transactions_by_address(asset_id=int(index), limit=int(limit), next_page=None, note_prefix=base64.b64decode(notePrefixB64), txn_type=txType,
        sig_type=sigType, txid=txid, block=int(block), min_round=int(minRound), max_round=int(maxRound),
        start_time=afterTime, end_time=beforeTime, min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan), address=account, address_role=addressRole,
        exclude_close_to=excludeCloseTo=="true")

@when('we make any LookupAccountTransactions call')
def txns_by_addr_any(context):
    context.response = context.icl.search_transactions_by_address("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI")

@then('the parsed LookupAccountTransactions response should be valid on round {roundNum}, and contain an array of len {length} and element number {idx} should have sender "{sender}"')
def parse_txns_by_addr(context, roundNum, length, idx, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(idx)]["sender"] == sender

@when('we make a Lookup Block call against round {block}')
def lookup_block(context, block):
    context.response = context.icl.block_info(int(block))

@when('we make any LookupBlock call')
def lookup_block_any(context):
    context.response = context.icl.block_info(12)

@then('the parsed LookupBlock response should have previous block hash "{prevHash}"')
def parse_lookup_block(context, prevHash):
    assert context.response["previous-block-hash"] == prevHash

@when('we make a Lookup Account by ID call against account "{account}" with round {block}')
def lookup_account(context, account, block):
    context.response = context.icl.account_info(account, int(block))

@when("we make any LookupAccountByID call")
def lookup_account_any(context):
    context.response = context.icl.account_info("PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI", 12)

@then('the parsed LookupAccountByID response should have address "{address}"')
def parse_account(context, address):
    assert context.response["account"]["address"] == address

@when('we make a Lookup Asset by ID call against asset index {index}')
def lookup_asset(context, index):
    context.response = context.icl.asset_info(int(index))

@when('we make any LookupAssetByID call')
def lookup_asset_any(context):
    context.response = context.icl.asset_info(1)

@then('the parsed LookupAssetByID response should have index {index}')
def parse_asset(context, index):
    assert context.response["asset"]["index"] == int(index)

@when('we make a Search Accounts call with assetID {index} limit {limit} currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} and round {block}')
def search_accounts(context, index, limit, currencyGreaterThan, currencyLessThan, block):
    context.response = context.icl.accounts(asset_id=int(index), limit=int(limit), next_page=None, min_balance=int(currencyGreaterThan),
        max_balance=int(currencyLessThan), block=int(block))

@when('we make any SearchAccounts call')
def search_accounts_any(context):
    context.response = context.icl.accounts(asset_id=2)

@then('the parsed SearchAccounts response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have address "{address}"')
def parse_accounts(context, roundNum, length, index, address):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["accounts"]) == int(length)
    if int(length) > 0:
        assert context.response["accounts"][int(index)]["address"] == address

@when('we make a Search For Transactions call with account "{account}" NotePrefix "{notePrefixB64}" TxType "{txType}" SigType "{sigType}" txid "{txid}" round {block} minRound {minRound} maxRound {maxRound} limit {limit} beforeTime "{beforeTime}" afterTime "{afterTime}" currencyGreaterThan {currencyGreaterThan} currencyLessThan {currencyLessThan} assetIndex {index} addressRole "{addressRole}" ExcluseCloseTo "{excludeCloseTo}"')
def search_txns(context, account, notePrefixB64, txType, sigType, txid, block, minRound, maxRound, limit, beforeTime, afterTime, currencyGreaterThan, currencyLessThan, index, addressRole, excludeCloseTo):
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
    context.response = context.icl.search_transactions(asset_id=int(index), limit=int(limit), next_page=None, note_prefix=base64.b64decode(notePrefixB64), txn_type=txType,
        sig_type=sigType, txid=txid, block=int(block), min_round=int(minRound), max_round=int(maxRound),
        start_time=afterTime, end_time=beforeTime, min_amount=int(currencyGreaterThan),
        max_amount=int(currencyLessThan), address=account, address_role=addressRole,
        exclude_close_to=excludeCloseTo=="true")

@when('we make any SearchForTransactions call')
def search_txns_any(context):
    context.response = context.icl.search_transactions(asset_id=2)

@then('the parsed SearchForTransactions response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have sender "{sender}"')
def parse_search_txns(context, roundNum, length, index, sender):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["transactions"]) == int(length)
    if int(length) > 0:
        assert context.response["transactions"][int(index)]["sender"] == sender

@when('we make a SearchForAssets call with limit {limit} creator "{creator}" name "{name}" unit "{unit}" index {index}')
def search_assets(context, limit, creator, name, unit, index):
    if creator == "none":
        creator = None
    if name == "none":
        name = None
    if unit == "none":
        unit = None
    
    context.response = context.icl.search_assets(limit=int(limit), 
        next_page=None, creator=creator, name=name, unit=unit,
        asset_id=int(index))

@when('we make any SearchForAssets call')
def search_assets_any(context):
    context.response = context.icl.search_assets(asset_id=2)

@then('the parsed SearchForAssets response should be valid on round {roundNum} and the array should be of len {length} and the element at index {index} should have asset index {assetIndex}')
def parse_search_assets(context, roundNum, length, index, assetIndex):
    assert context.response["current-round"] == int(roundNum)
    assert len(context.response["assets"]) == int(length)
    if int(length) > 0:
        assert context.response["assets"][int(index)]["index"] == int(assetIndex)

@when('we make any Suggested Transaction Parameters call')
def suggested_any(context):
    context.response = context.acl.suggested_params()

@then('the parsed Suggested Transaction Parameters response should have first round valid of {roundNum}')
def parse_suggested(context, roundNum):
    assert context.response.first == int(roundNum)

@then('expect the path used to be "{path}"')
def expect_path(context, path):
    context.server.shutdown()
    exp_path, exp_query = urllib.parse.splitquery(path)
    exp_query = urllib.parse.parse_qs(exp_query)

    actual_path, actual_query = urllib.parse.splitquery(context.response["path"])
    actual_query = urllib.parse.parse_qs(actual_query)
    
    assert exp_path == actual_path
    assert exp_query == actual_query

@then('expect error string to contain "{err}"')
def expect_error(context, err):
    context.server.shutdown()


    
