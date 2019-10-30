from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import base64
from . import error
from . import encoding
from . import constants


class AlgodClient:
    """
    Client class for kmd. Handles all algod requests.

    Args:
        algod_token (str): algod API token
        algod_address (str): algod address
        headers (dict, optional): extra header name/value for all requests

    Attributes:
        algod_token (str)
        algod_address (str)
        headers (dict)
    """
    def __init__(self, algod_token, algod_address, headers=None):
        self.algod_token = algod_token
        self.algod_address = algod_address
        self.headers = headers

    def algod_request(self, method, requrl, params=None, data=None,
                      headers=None):
        """
        Execute a given request.

        Args:
            method (str): request method
            requrl (str): url for the request
            params (dict, optional): parameters for the request
            data (dict, optional): data in the body of the request
            headers (dict, optional): additional header for request

        Returns:
            dict: loaded from json response body
        """
        header = {}

        if self.headers:
            header.update(self.headers)

        if headers:
            header.update(headers)

        if requrl not in constants.no_auth:
            header.update({
                constants.algod_auth_header: self.algod_token
                })

        if requrl not in constants.unversioned_paths:
            requrl = constants.api_version_path_prefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)

        req = Request(self.algod_address+requrl, headers=header, method=method,
                      data=data)

        try:
            resp = urlopen(req)
        except urllib.error.HTTPError as e:
            e = e.read().decode("utf-8")
            try:
                raise error.AlgodHTTPError(json.loads(e)["message"])
            except:
                raise error.AlgodHTTPError(e)
        return json.loads(resp.read().decode("utf-8"))

    def status(self, **kwargs):
        """Return node status."""
        req = "/status"
        return self.algod_request("GET", req, **kwargs)

    def health(self, **kwargs):
        """Return null if the node is running."""
        req = "/health"
        return self.algod_request("GET", req, **kwargs)

    def status_after_block(self, block_num, **kwargs):
        """
        Return node status immediately after blockNum.

        Args:
            block_num: block number
        """
        req = "/status/wait-for-block-after/" + str(block_num)
        return self.algod_request("GET", req, **kwargs)

    def pending_transactions(self, max_txns=0, **kwargs):
        """
        Return pending transactions.

        Args:
            max_txns (int): maximum number of transactions to return;
                if max_txns is 0, return all pending transactions
        """
        query = {"max": max_txns}
        req = "/transactions/pending"
        return self.algod_request("GET", req, params=query, **kwargs)

    def versions(self, **kwargs):
        """Return algod versions."""
        req = "/versions"
        return self.algod_request("GET", req, **kwargs)

    def ledger_supply(self, **kwargs):
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algod_request("GET", req, **kwargs)

    def transactions_by_address(self, address, first=None, last=None,
                                limit=None, from_date=None, to_date=None,
                                **kwargs):
        """
        Return transactions for an address. If indexer is not enabled, you can
        search by date and you do not have to specify first and last rounds.

        Args:
            address (str): account public key
            first (int, optional): no transactions before this block will be
                returned
            last (int, optional): no transactions after this block will be
                returned; defaults to last round
            limit (int, optional): maximum number of transactions to return;
                default is 100
            from_date (str, optional): no transactions before this date will be
                returned; format YYYY-MM-DD
            to_date (str, optional): no transactions after this date will be
                returned; format YYYY-MM-DD
        """
        query = dict()
        if first is not None:
            query["firstRound"] = first
        if last is not None:
            query["lastRound"] = last
        if limit is not None:
            query["max"] = limit
        if to_date is not None:
            query["toDate"] = to_date
        if from_date is not None:
            query["fromDate"] = from_date
        req = "/account/" + address + "/transactions"
        return self.algod_request("GET", req, params=query, **kwargs)

    def account_info(self, address, **kwargs):
        """
        Return account information.

        Args:
            address (str): account public key
        """
        req = "/account/" + address
        return self.algod_request("GET", req, **kwargs)

    def asset_info(self, index, **kwargs):
        """
        Return asset information.

        Args:
            index (int): asset index
        """
        req = "/asset/" + str(index)
        return self.algod_request("GET", req, **kwargs)

    def list_assets(self, max_index=None, max_assets=None, **kwargs):
        """
        Return a list of up to max_assets assets, where the maximum asset
        index is max_index.

        Args:
            max_index (int, optional): maximum asset index; defaults to 0,
                which lists most recent assets
            max_assets (int, optional): maximum number of assets (0 to 100);
                defaults to 100
        """
        query = dict()
        query["assetIdx"] = max_index if max_index is not None else 0
        query["max"] = max_assets if max_assets is not None else 100
        req = "/assets"
        return self.algod_request("GET", req, params=query, **kwargs)

    def transaction_info(self, address, transaction_id, **kwargs):
        """
        Return transaction information.

        Args:
            address (str): account public key
            transaction_id (str): transaction ID
        """
        req = "/account/" + address + "/transaction/" + transaction_id
        return self.algod_request("GET", req, **kwargs)

    def pending_transaction_info(self, transaction_id, **kwargs):
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transactions/pending/" + transaction_id
        return self.algod_request("GET", req, **kwargs)

    def transaction_by_id(self, transaction_id, **kwargs):
        """
        Return transaction information; only works if indexer is enabled.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transaction/" + transaction_id
        return self.algod_request("GET", req, **kwargs)

    def suggested_fee(self, **kwargs):
        """Return suggested transaction fee."""
        req = "/transactions/fee"
        return self.algod_request("GET", req, **kwargs)

    def suggested_params(self, **kwargs):
        """Return suggested transaction parameters."""
        req = "/transactions/params"
        return self.algod_request("GET", req, **kwargs)

    def send_raw_transaction(self, txn, **kwargs):
        """
        Broadcast a signed transaction to the network.

        Args:
            txn (str): transaction to send, encoded in base64
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        txn = base64.b64decode(txn)
        req = "/transactions"
        return self.algod_request("POST", req, data=txn, **kwargs)["txId"]

    def send_transaction(self, txn, **kwargs):
        """
        Broadcast a signed transaction object to the network.

        Args:
            txn (SignedTransaction or MultisigTransaction): transaction to send
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        return self.send_raw_transaction(encoding.msgpack_encode(txn),
                                         **kwargs)

    def send_transactions(self, txns, **kwargs):
        """
        Broadcast list of a signed transaction objects to the network.

        Args:
            txns (SignedTransaction[] or MultisigTransaction[]):
                transactions to send
            request_header (dict, optional): additional header for request

        Returns:
            str: first transaction ID
        """
        serialized = []
        for txn in txns:
            serialized.append(base64.b64decode(encoding.msgpack_encode(txn)))

        return self.send_raw_transaction(base64.b64encode(
                                         b''.join(serialized)), **kwargs)

    def block_info(self, round, **kwargs):
        """
        Return block information.

        Args:
            round (int): block number
        """
        req = "/block/" + str(round)
        return self.algod_request("GET", req, **kwargs)
