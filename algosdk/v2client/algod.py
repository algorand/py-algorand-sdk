from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import base64
from .. import error
from .. import encoding
from .. import constants
from .. import future
import msgpack

api_version_path_prefix = "/v2"


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
                      headers=None, response_format="json"):
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
            requrl = api_version_path_prefix + requrl
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
        res = resp.read().decode("utf-8")
        if response_format == "json":
            return json.loads(res) if res else None
        else:
            return base64.b64decode(res)

    def account_info(self, address, **kwargs):
        """
        Return account information.

        Args:
            address (str): account public key
        """
        req = "/accounts/" + address
        return self.algod_request("GET", req, **kwargs)

    def pending_transactions_by_address(self, address, limit=0, response_format="json",
                                        **kwargs):
        """
        Get the list of pending transactions by address, sorted by priority,
        in decreasing order, truncated at the end at MAX. If MAX = 0, returns
        all pending transactions.

        Args:
            address (str): account public key
            limit (int, optional): maximum number of transactions to return
            response_format (str): the format in which the response is returne: either
                "json" or "msgpack"
        """
        query = {"format": response_format}
        if limit:
            query["max"] = limit
        req = "/accounts/" + address + "/transactions/pending"
        res = self.algod_request(
            "GET", req, params=query, response_format=response_format, 
            **kwargs)
        if response_format == "msgpack":
            res = msgpack.unpackb(res, raw=False)
            for i in range(len(res["top-transactions"])):
                res["top-transactions"][i] = encoding.msgpack_decode(
                    res["top-transactions"][i])
        print(res)
        return res

    def block_info(self, block, response_format="json", **kwargs):
        """
        Get the block for the given round.

        Args:
            block (int): block number
            response_format (str): the format in which the response is returne: either
                "json" or "msgpack"
        """
        query = {"format": response_format}
        req = "/blocks/" + str(block)
        res = self.algod_request("GET", req, query, response_format=response_format, **kwargs)
        if response_format == "msgpack":
            res = msgpack.unpackb(res, raw=False)
        return res


    def ledger_supply(self, **kwargs):
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algod_request("GET", req, **kwargs)

    def status(self, **kwargs):
        """Return node status."""
        req = "/status"
        return self.algod_request("GET", req, **kwargs)

    def status_after_block(self, block_num, **kwargs):
        """
        Return node status immediately after blockNum.

        Args:
            block_num: block number
        """
        req = "/status/wait-for-block-after/" + str(block_num)
        return self.algod_request("GET", req, **kwargs)

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

    def shutdown(self, timeout=0, **kwargs):
        """
        Shut down the node.

        Args:
            timeout (int): number of seconds after which the node should begin
                shutting down
        """
        req = "/shutdown"
        query = dict()
        if timeout:
            query["timeout"] = timeout
        return self.algod_request("GET", req, query, **kwargs)

    def register_participation_keys(
        self, address="all", fee=None, key_dilution=None,
        last_valid_round=None, no_wait=False, **kwargs):
        """
        Generate or renew and register participation keys on the node for a
        given account address.
        
        Args:
            address (str, optional): the account to update; if unspecified,
                update all accounts
            fee (int, optional): the fee to use when submitting key
                registration transactions; defaults to the suggested fee
            key_dilution (int, optional): value to use for two-level
                participation key
            last_valid_round (int, optional): the last round for which the
                generated participation keys will be valid
            no_wait (bool, optional): don't wait for transaction to commit
                before returning response
        """
        req = "/register-participation-keys/" + address
        query = dict()
        if fee:
            query["fee"] = fee
        if key_dilution:
            query["key-dilution"] = key_dilution
        if last_valid_round:
            query["round-last-valid"] = last_valid_round
        if no_wait:
            query["no-wait"] = "true"
        
        return self.algod_request("POST", req, query, **kwargs)


    def pending_transactions(self, max_txns=0, response_format="json", **kwargs):
        """
        Return pending transactions.

        Args:
            max_txns (int): maximum number of transactions to return;
                if max_txns is 0, return all pending transactions
            response_format (str): the format in which the response is returne: either
                "json" or "msgpack"
        """
        query = {"format": response_format}
        if max_txns:
            query["max"] = max_txns
        req = "/transactions/pending"
        res = self.algod_request("GET", req, params=query, response_format=response_format, **kwargs)
        if response_format == "msgpack":
            res = msgpack.unpackb(res, raw=False)
            for i in range(len(res["top-transactions"])):
                res["top-transactions"][i] = encoding.msgpack_decode(
                    res["top-transactions"][i])
        print(res)
        return res

    def pending_transaction_info(self, transaction_id, response_format="json", **kwargs):
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
            response_format (str): the format in which the response is returne: either
                "json" or "msgpack"
        """
        req = "/transactions/pending/" + transaction_id
        query = {"format": response_format}
        res = self.algod_request("GET", req, params=query, response_format=response_format, **kwargs)
        if response_format == "msgpack":
            res = msgpack.unpackb(res, raw=False)
            res["txn"] = encoding.msgpack_decode(res["txn"])
        print(res)
        return res

    def health(self, **kwargs):
        """Return null if the node is running."""
        req = "/health"
        return self.algod_request("GET", req, **kwargs)
    
    def versions(self, **kwargs):
        """Return algod versions."""
        req = "/versions"
        return self.algod_request("GET", req, **kwargs)

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

    def suggested_params(self, **kwargs):
        """Return suggested transaction parameters."""
        req = "/transactions/params"
        res = self.algod_request("GET", req, **kwargs)

        return future.transaction.SuggestedParams(
            res["fee"],
            res["last-round"],
            res["last-round"] + 1000,
            res["genesis-hash"],
            res["genesis-id"],
            False,
            res["consensus-version"],
            res["min-fee"]
            )