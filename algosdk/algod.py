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

    Attributes:
        algod_token (str)
        algod_address (str)
    """
    def __init__(self, algod_token, algod_address):
        self.algod_token = algod_token
        self.algod_address = algod_address

    def algod_request(self, method, requrl, params=None, data=None):
        """
        Execute a given request.

        Args:
            method (str): request method
            requrl (str): url for the request
            params (dict, optional): parameters for the request
            data (dict, optional): data in the body of the request

        Returns:
            dict: loaded from json response body
        """
        if requrl in constants.no_auth:
            header = {}
        else:
            header = {
                constants.algod_auth_header: self.algod_token
                }

        if requrl not in constants.unversioned_paths:
            requrl = constants.api_version_path_prefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)

        req = Request(self.algod_address+requrl, headers=header, method=method,
                      data=data)

        try:
            resp = urlopen(req)
        except urllib.error.HTTPError as e:
            e = e.read().decode("ascii")
            try:
                raise error.AlgodHTTPError(json.loads(e)["message"])
            except:
                raise error.AlgodHTTPError(e)
        return json.loads(resp.read().decode("ascii"))

    def status(self):
        """
        Return node status.
        """
        req = "/status"
        return self.algod_request("GET", req)

    def health(self):
        """
        Return null if the node is running.
        """
        req = "/health"
        return self.algod_request("GET", req)

    def status_after_block(self, block_num):
        """
        Return node status immediately after blockNum.

        Args:
            block_num: block number
        """
        req = "/status/wait-for-block-after/" + str(block_num)
        return self.algod_request("GET", req)

    def pending_transactions(self, max_txns=0):
        """
        Return up to max_txns pending transactions;

        Args:
            max_txns (int): maximum number of transactions to return;
                if max_txns is 0, return all pending transactions
        """
        query = {"max": max_txns}
        req = "/transactions/pending"
        return self.algod_request("GET", req, params=query)

    def versions(self):
        """Return algod versions."""
        req = "/versions"
        return self.algod_request("GET", req)

    def ledger_supply(self):
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algod_request("GET", req)

    def transactions_by_address(self, address, first=1, last=None, limit=0,
                                from_date=None, to_date=None):
        """
        Return transactions for an address. If indexer is enabled, can search
        by date.

        Args:
            address (str): account public key
            first (int, optional): no transactions before this block will be
                returned
            last (int, optional): no transactions after this block will be
                returned; defaults to last round
            limit (int, optional): maximum number of transactions to return;
                if limit is 0, return all
            from_date (str, optional): no transactions before this date will be
                returned; format YYYY-MM-DD
            to_date (str, optional): no transactions after this date will be
                returned; format YYYY-MM-DD
        """
        if not last:
            last = self.status()["lastRound"]
        query = {"firstRound": first, "lastRound": last}
        if limit != 0:
            query["max"] = limit
        if to_date:
            query["toDate"] = to_date
        if from_date:
            query["fromDate"] = from_date
        req = "/account/" + address + "/transactions"
        return self.algod_request("GET", req, params=query)

    def account_info(self, address):
        """
        Return account information.

        Args:
            address (str): account public key
        """
        req = "/account/" + address
        return self.algod_request("GET", req)

    def transaction_info(self, address, transaction_id):
        """
        Return transaction information.

        Args:
            address (str): account public key
            transaction_id (str): transaction ID
        """
        req = "/account/" + address + "/transaction/" + transaction_id
        return self.algod_request("GET", req)

    def pending_transaction_info(self, transaction_id):
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transactions/pending/" + transaction_id
        return self.algod_request("GET", req)

    def transaction_by_id(self, transaction_id):
        """
        Return transaction information; only works if indexer is enabled.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transaction/" + transaction_id
        return self.algod_request("GET", req)

    def suggested_fee(self):
        """Return suggested transaction fee."""
        req = "/transactions/fee"
        return self.algod_request("GET", req)

    def suggested_params(self):
        """Return suggested transaction paramters."""
        req = "/transactions/params"
        return self.algod_request("GET", req)

    def send_raw_transaction(self, signed_txn):
        """
        Broadcast a signed transaction object to the network.

        Args:
            signed_txn (SignedTransaction): transaction to be sent

        Returns:
            str: transaction ID
        """
        signed_txn = encoding.msgpack_encode(signed_txn)
        signed_txn = base64.b64decode(signed_txn)
        req = "/transactions"
        return self.algod_request("POST", req, data=signed_txn)["txId"]

    def block_info(self, round):
        """
        Return block information.

        Args:
            round (int): block number
        """
        req = "/block/" + str(round)
        return self.algod_request("GET", req)
