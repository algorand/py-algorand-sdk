from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import base64
from .. import error
from .. import encoding
from .. import constants
from .. import transaction


class IndexerClient:
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

    def accounts(
        self, asset_id=None, limit=None, next_page=None, min_balance=None,
        max_balance=None, round=None, **kwargs):
        """
        Return accounts that hold the asset; microalgos are the default
        currency unless asset_id is specified, in which case the asset will
        be used.

        Args:
            asset_id (str, optional): include accounts holding this asset
            limit (int, optional): maximum number of results to return
            next_page (str, optional): the next page of results; use the next
                token provided by the previous results
            min_balance (int, optional): results should have an amount greater
                than this value
            max_balance (int, optional): results should have an amount less
            round (int, optional): include results for the specified round;
                for performance reasons, this parameter may be disabled on
                some configurations
        """
        req = "/accounts"
        query = dict()
        if asset_id:
            query["asset-id"] = asset_id
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page
        if min_balance:
            query["currency-greater-than"] = min_balance
        if max_balance:
            query["currency-less-than"] = max_balance
        if round:
            query["round"] = round
        return self.algod_request("GET", req, **kwargs)

    def block_info(self, round, **kwargs):
        """
        Get the block for the given round.

        Args:
            round (int): block number
        """
        query = {"format": format}
        req = "/blocks/" + str(round)
        return self.algod_request("GET", req, query, **kwargs)

    def account_info(self, address, round=None, **kwargs):
        """
        Return account information.

        Args:
            address (str): account public key
            round (int, optional): use results from the specified round
        """
        req = "/accounts/" + address
        query = dict()
        if round:
            query["account-id"] = round
        return self.algod_request("GET", req, **kwargs)

    def search_transactions(
        self, limit=None, next_page=None, note_prefix=None, txn_type=None,
        sig_type=None, txid=None, round=None, min_round=None, max_round=None,
        asset_id=None, start_time=None, end_time=None, min_amount=None,
        max_amount=None, address=None, address_role=None,
        exclude_close_to=False, **kwargs):
        """
        Return a list of transactions satisfying the conditions.

        Args:
            limit (int, optional): maximum number of results to return
            next_page (str, optional): the next page of results; use the next
                token provided by the previous results
            note_prefix (bytes, optional): specifies a prefix which must be
                contained in the note field
            txn_type (str, optional): type of transaction; one of "pay",
                "keyreg", "acfg", "axfer", "afrz"
            sig_type (str, optional): type of signature; one of "sig", "msig",
                "lsig"
            txid (str, optional): lookup a specific transaction by ID
            round (int, optional): include results for the specified round
            min_round (int, optional): include results at or after the
                specified round
            max_round (int, optional): include results at or before the
                specified round
            asset_id (int, optional): include transactions for the specified
                asset
            start_time (str, optional): include results before the given time;
                must be an RFC 3339 formatted string
            end_time (str, optional): include results after the given time;
                must be an RFC 3339 formatted string
            min_amount (int, optional): results should have an amount greater
                than this value; microalgos are the default currency unless an
                asset-id is provided, in which case the asset will be used
            max_amount (int, optional): results should have an amount less
                than this value, microalgos are the default currency unless an
                asset-id is provided, in which case the asset will be used
            address (str, optional): only include transactions with this
                address in one of the transaction fields
            address_role (str, optional): one of "sender" or "receiver";
                combine with the address parameter to define what type of
                address to search for
            exclude_close_to (bool, optional): combine with address and
                address_role parameters to define what type of address to
                search for; the close to fields are normally treated as a
                receiver, if you would like to exclude them set this parameter
                to true
        """



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

