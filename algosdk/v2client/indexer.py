from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import base64
from .. import error
from .. import encoding
from .. import constants

api_version_path_prefix = "/v2"


class IndexerClient:
    """
    Client class for indexer. Handles all indexer requests.

    Args:
        indexer_token (str): indexer API token
        indexer_address (str): indexer address
        headers (dict, optional): extra header name/value for all requests

    Attributes:
        indexer_token (str)
        indexer_address (str)
        headers (dict)
    """

    def __init__(self, indexer_token, indexer_address, headers=None):
        self.indexer_token = indexer_token
        self.indexer_address = indexer_address
        self.headers = headers

    def indexer_request(self, method, requrl, params=None, data=None,
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

        if (requrl not in constants.no_auth) and self.indexer_token:
            header.update({
                constants.indexer_auth_header: self.indexer_token
            })

        if requrl not in constants.unversioned_paths:
            requrl = api_version_path_prefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)

        req = Request(self.indexer_address+requrl, headers=header, method=method,
                      data=data)

        try:
            resp = urlopen(req)
        except urllib.error.HTTPError as e:
            e = e.read().decode("utf-8")
            try:
                raise error.IndexerHTTPError(json.loads(e)["message"])
            except:
                raise error.IndexerHTTPError(e)
        response_dict = json.loads(resp.read().decode("utf-8"))

        def recursively_sort_dict(dictionary):
            return {k: recursively_sort_dict(v) if isinstance(v, dict) else v
                    for k, v in sorted(dictionary.items())}
        response_dict = recursively_sort_dict(response_dict)

        # additionally, if there are any lists-of-dicts in the response, sort that list based on
        # the value corresponding to key['key']
        # this sorts things like application apps global-state

        def recursively_sort_on_key(dictionary):
            for k, v in sorted(dictionary.items()):
                if isinstance(v, list) and all(isinstance(item, dict) for item in v):
                    if all(hasattr(item, 'key') for item in v):
                        from operator import itemgetter
                        dictionary[k] = sorted(v, key=itemgetter('key')) # need to turn this into a return
                    else:
                        for item in v:
                            recursively_sort_on_key(item)
        recursively_sort_on_key(response_dict)
        # for k, v in response_dict.items():
        #     if isinstance(v, list):
        #         if all(isinstance(item, dict) and hasattr(item, 'key') for item in v):
        #             from operator import itemgetter
        #             response_dict[k] = sorted(v, key=itemgetter('key'))
        #         else:
        #             #sort_on_key(dict)
        #             pass
        return response_dict

    def health(self, **kwargs):
        """Return 200 and a simple status message if the node is running."""
        req = "/health"
        return self.indexer_request("GET", req, **kwargs)

    def accounts(
        self, asset_id=None, limit=None, next_page=None, min_balance=None,
        max_balance=None, block=None, auth_addr=None, application_id=None, **kwargs):
        """
        Return accounts that match the search; microalgos are the default
        currency unless asset_id is specified, in which case the asset will
        be used.

        Args:
            asset_id (int, optional): include accounts holding this asset
            limit (int, optional): maximum number of results to return
            next_page (str, optional): the next page of results; use the next
                token provided by the previous results
            min_balance (int, optional): results should have an amount greater
                than this value
            max_balance (int, optional): results should have an amount less
            block (int, optional): include results for the specified round;
                for performance reasons, this parameter may be disabled on
                some configurations
            auth_addr (str, optional): Include accounts configured to use
                this spending key.
            application_id (int, optional): results should filter on this application

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
        if block:
            query["round"] = block
        if auth_addr:
            query["auth-addr"] = auth_addr
        if application_id:
            query["application-id"] = application_id
        return self.indexer_request("GET", req, query, **kwargs)

    def asset_balances(self, asset_id, limit=None, next_page=None, min_balance=None,
        max_balance=None, block=None, **kwargs):
        """
        Return accounts that hold the asset; microalgos are the default
        currency unless asset_id is specified, in which case the asset will
        be used.

        Args:
            asset_id (int): include accounts holding this asset
            limit (int, optional): maximum number of results to return
            next_page (str, optional): the next page of results; use the next
                token provided by the previous results
            min_balance (int, optional): results should have an amount greater
                than this value
            max_balance (int, optional): results should have an amount less
            block (int, optional): include results for the specified round;
                for performance reasons, this parameter may be disabled on
                some configurations
        """
        req = "/assets/" + str(asset_id) + "/balances"
        query = dict()
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page
        if min_balance:
            query["currency-greater-than"] = min_balance
        if max_balance:
            query["currency-less-than"] = max_balance
        if block:
            query["round"] = block
        return self.indexer_request("GET", req, query, **kwargs)

    def block_info(self, block, **kwargs):
        """
        Get the block for the given round.

        Args:
            block (int): block number
        """
        req = "/blocks/" + str(block)
        return self.indexer_request("GET", req, **kwargs)

    def account_info(self, address, block=None, **kwargs):
        """
        Return account information.

        Args:
            address (str): account public key
            block (int, optional): use results from the specified round
        """
        req = "/accounts/" + address
        query = dict()
        if block:
            query["round"] = block
        return self.indexer_request("GET", req, query, **kwargs)

    def search_transactions(
        self, limit=None, next_page=None, note_prefix=None, txn_type=None,
        sig_type=None, txid=None, block=None, min_round=None, max_round=None,
        asset_id=None, start_time=None, end_time=None, min_amount=None,
        max_amount=None, address=None, address_role=None,
        exclude_close_to=False, application_id=None, rekey_to=False, **kwargs):
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
            block (int, optional): include results for the specified round
            min_round (int, optional): include results at or after the
                specified round
            max_round (int, optional): include results at or before the
                specified round
            asset_id (int, optional): include transactions for the specified
                asset
            end_time (str, optional): include results before the given time;
                must be an RFC 3339 formatted string
            start_time (str, optional): include results after the given time;
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
            application_id (int, optional): filter for transactions pertaining
                to an application
            rekey_to (bool, optional) Include results which include the
                rekey-to field.
        """
        req = "/transactions"
        query = dict()
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page
        if note_prefix:
            query["note-prefix"] = base64.b64encode(note_prefix).decode()
        if txn_type:
            query["tx-type"] = txn_type
        if sig_type:
            query["sig-type"] = sig_type
        if txid:
            query["txid"] = txid
        if block:
            query["round"] = block
        if min_round:
            query["min-round"] = min_round
        if max_round:
            query["max-round"] = max_round
        if asset_id:
            query["asset-id"] = asset_id
        if end_time:
            query["before-time"] = end_time
        if start_time:
            query["after-time"] = start_time
        if min_amount:
            query["currency-greater-than"] = min_amount
        if max_amount:
            query["currency-less-than"] = max_amount
        if address:
            query["address"] = address
        if address_role:
            query["address-role"] = address_role
        if exclude_close_to:
            query["exclude-close-to"] = "true"
        if application_id:
            query["application-id"] = application_id
        if rekey_to:
            query["rekey-to"] = "true"


        return self.indexer_request("GET", req, query, **kwargs)

    def search_transactions_by_address(
        self, address, limit=None, next_page=None, note_prefix=None,
        txn_type=None, sig_type=None, txid=None, block=None, min_round=None,
        max_round=None, asset_id=None, start_time=None, end_time=None,
        min_amount=None, max_amount=None, rekey_to=False, **kwargs):
        """
        Return a list of transactions satisfying the conditions for the address.

        Args:
            address (str): only include transactions with this
                address in one of the transaction fields
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
            block (int, optional): include results for the specified round
            min_round (int, optional): include results at or after the
                specified round
            max_round (int, optional): include results at or before the
                specified round
            asset_id (int, optional): include transactions for the specified
                asset
            end_time (str, optional): include results before the given time;
                must be an RFC 3339 formatted string
            start_time (str, optional): include results after the given time;
                must be an RFC 3339 formatted string
            min_amount (int, optional): results should have an amount greater
                than this value; microalgos are the default currency unless an
                asset-id is provided, in which case the asset will be used
            max_amount (int, optional): results should have an amount less
                than this value, microalgos are the default currency unless an
                asset-id is provided, in which case the asset will be used
            rekey_to (bool, optional) Include results which include the
                rekey-to field.
        """
        req = "/accounts/" + address + "/transactions"
        query = dict()
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page
        if note_prefix:
            query["note-prefix"] = base64.b64encode(note_prefix).decode()
        if txn_type:
            query["tx-type"] = txn_type
        if sig_type:
            query["sig-type"] = sig_type
        if txid:
            query["txid"] = txid
        if block:
            query["round"] = block
        if min_round:
            query["min-round"] = min_round
        if max_round:
            query["max-round"] = max_round
        if asset_id:
            query["asset-id"] = asset_id
        if end_time:
            query["before-time"] = end_time
        if start_time:
            query["after-time"] = start_time
        if min_amount:
            query["currency-greater-than"] = min_amount
        if max_amount:
            query["currency-less-than"] = max_amount
        if rekey_to:
            query["rekey-to"] = "true"

        return self.indexer_request("GET", req, query, **kwargs)

    def search_asset_transactions(self, asset_id, limit=None, next_page=None, note_prefix=None,
        txn_type=None, sig_type=None, txid=None, block=None, min_round=None,
        max_round=None, address=None, start_time=None, end_time=None,
        min_amount=None, max_amount=None, address_role=None,
        exclude_close_to=False, rekey_to=False, **kwargs):
        """
        Return a list of transactions satisfying the conditions for the address.

        Args:
            asset_id (int): include transactions for the specified
                asset
                
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
            block (int, optional): include results for the specified round
            min_round (int, optional): include results at or after the
                specified round
            max_round (int, optional): include results at or before the
                specified round
            address (str, optional): only include transactions with this
                address in one of the transaction fields
            end_time (str, optional): include results before the given time;
                must be an RFC 3339 formatted string
            start_time (str, optional): include results after the given time;
                must be an RFC 3339 formatted string
            min_amount (int, optional): results should have an amount greater
                than this value; microalgos are the default currency unless an
                asset-id is provided, in which case the asset will be used
            max_amount (int, optional): results should have an amount less
                than this value, microalgos are the default currency unless an
                asset-id is provided, in which case the asset will be used
            address_role (str, optional): one of "sender" or "receiver";
                combine with the address parameter to define what type of
                address to search for
            exclude_close_to (bool, optional): combine with address and
                address_role parameters to define what type of address to
                search for; the close to fields are normally treated as a
                receiver, if you would like to exclude them set this parameter
                to true
            rekey_to (bool, optional) Include results which include the
                rekey-to field.
        """
        req = "/assets/" + str(asset_id) + "/transactions"
        query = dict()
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page
        if note_prefix:
            query["note-prefix"] = base64.b64encode(note_prefix).decode()
        if txn_type:
            query["tx-type"] = txn_type
        if sig_type:
            query["sig-type"] = sig_type
        if txid:
            query["txid"] = txid
        if block:
            query["round"] = block
        if min_round:
            query["min-round"] = min_round
        if max_round:
            query["max-round"] = max_round
        if end_time:
            query["before-time"] = end_time
        if start_time:
            query["after-time"] = start_time
        if min_amount:
            query["currency-greater-than"] = min_amount
        if max_amount:
            query["currency-less-than"] = max_amount
        if address:
            query["address"] = address
        if address_role:
            query["address-role"] = address_role
        if exclude_close_to:
            query["exclude-close-to"] = "true"
        if rekey_to:
            query["rekey-to"] = "true"

        return self.indexer_request("GET", req, query, **kwargs)

    def search_assets(
        self, limit=None, next_page=None, creator=None, name=None, unit=None,
        asset_id=None, **kwargs):
        """
        Return assets that satisfy the conditions.

        Args:
            limit (int, optional): maximum number of results to return
            next_page (str, optional): the next page of results; use the next
                token provided by the previous results
            creator (str, optional): filter just assets with the given creator
                address
            name (str, optional): filter just assets with the given name
            unit (str, optional): filter just assets with the given unit
            asset_id (int, optional): return only the asset with this ID
        """
        req = "/assets"
        query = dict()
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page
        if creator:
            query["creator"] = creator
        if name:
            query["name"] = name
        if unit:
            query["unit"] = unit
        if asset_id:
            query["asset-id"] = asset_id

        return self.indexer_request("GET", req, query, **kwargs)

    def asset_info(self, asset_id, **kwargs):
        """
        Return asset information.

        Args:
            asset_id (int): asset index
        """
        req = "/assets/" + str(asset_id)
        return self.indexer_request("GET", req, **kwargs)

    def applications(
            self, application_id, round=None, **kwargs):
        """
        Return applications that satisfy the conditions.

        Args:
            application_id (int): application index
            round (int, optional): restrict search to passed round
        """
        req = "/applications/" + str(application_id)
        query = dict()
        if round:
            query["round"] = round

        return self.indexer_request("GET", req, query, **kwargs)

    def search_applications(
            self, application_id=None, round=None, limit=None, next_page=None, **kwargs):
        """
        Return applications that satisfy the conditions.

        Args:
            application_id (int, optional): restrict search to application index
            round (int, optional): restrict search to passed round
            limit (int, optional): restrict number of results to limit
            next_page (string, optional): used for pagination
        """
        req = "/applications"
        query = dict()
        if application_id:
            query["application-id"] = application_id
        if round:
            query["round"] = round
        if limit:
            query["limit"] = limit
        if next_page:
            query["next"] = next_page

        return self.indexer_request("GET", req, query, **kwargs)
