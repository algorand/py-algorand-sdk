import base64
import json
from typing import (
    Any,
    Dict,
    Final,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)
import urllib.error
from urllib import parse
from urllib.request import Request, urlopen

from algosdk import constants, encoding, error, transaction, util

api_version_path_prefix = "/v2"


ParamsType = Union[
    Mapping[Any, Any],
    Mapping[Any, Sequence[Any]],
    Sequence[Tuple[Any, Any]],
    Sequence[Tuple[Any, Sequence[Any]]],
]


class AlgodClient:
    """
    Client class for algod. Handles all algod requests.

    Args:
        algod_token (str): algod API token
        algod_address (str): algod address
        headers (dict, optional): extra header name/value for all requests

    Attributes:
        algod_token (str)
        algod_address (str)
        headers (dict)
    """

    def __init__(
        self,
        algod_token: str,
        algod_address: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.algod_token: Final[str] = algod_token
        self.algod_address: Final[str] = algod_address
        self.headers: Final[Optional[Dict[str, str]]] = headers

    def algod_request(
        self,
        method: str,
        requrl: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[bytes, Iterable[bytes]]] = None,
        headers: Optional[Dict[str, str]] = None,
        response_format: Optional[str] = "json",
    ) -> Any:
        """
        Execute a given request.

        Args:
            method (str): request method
            requrl (str): url for the request
            params (ParamsType, optional): parameters for the request
            data (bytes, optional): data in the body of the request
            headers (dict, optional): additional header for request
            response_format (str, optional): format of the response

        Returns:
            dict: loaded from json response body
        """
        header = {"User-Agent": "py-algorand-sdk"}

        if self.headers:
            header.update(self.headers)

        if headers:
            header.update(headers)

        if requrl not in constants.no_auth:
            header.update({constants.algod_auth_header: self.algod_token})

        if requrl not in constants.unversioned_paths:
            requrl = api_version_path_prefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)

        req = Request(
            self.algod_address + requrl,
            headers=header,
            method=method,
            data=data,
        )

        try:
            resp = urlopen(req)
        except urllib.error.HTTPError as e:
            code = e.code
            es = e.read().decode("utf-8")
            try:
                e = json.loads(es)["message"]
            finally:
                raise error.AlgodHTTPError(e, code)
        if response_format == "json":
            try:
                return json.load(resp)
            except Exception as e:
                raise error.AlgodResponseError(
                    "Failed to parse JSON response from algod"
                ) from e
        else:
            return resp.read()

    def account_info(
        self, address: str, exclude: Optional[bool] = None, **kwargs: Any
    ) -> Any:
        """
        Return account information.

        Args:
            address (str): account public key
        """
        query = {}
        if exclude:
            query["exclude"] = exclude
        req = "/accounts/" + address
        return self.algod_request("GET", req, query, **kwargs)

    def asset_info(self, asset_id: int, **kwargs: Any) -> Any:
        """
        Return information about a specific asset.

        Args:
            asset_id (int): The ID of the asset to look up.
        """
        req = "/assets/" + str(asset_id)
        return self.algod_request("GET", req, **kwargs)

    def application_info(self, application_id: int, **kwargs: Any) -> Any:
        """
        Return information about a specific application.

        Args:
            application_id (int): The ID of the application to look up.
        """
        req = "/applications/" + str(application_id)
        return self.algod_request("GET", req, **kwargs)

    def application_box_by_name(
        self, application_id: int, box_name: bytes, **kwargs: Any
    ) -> Any:
        """
        Return the value of an application's box.

        NOTE: box values are returned as base64-encoded strings.

        Args:
            application_id (int): The ID of the application to look up.
            box_name (bytes): The name or key of the box.
        """
        encoded_box = base64.b64encode(box_name).decode()
        box_name_encoded = "b64:" + encoded_box
        req = "/applications/" + str(application_id) + "/box"
        params = {"name": box_name_encoded}
        return self.algod_request("GET", req, params=params, **kwargs)

    def application_boxes(
        self, application_id: int, limit: int = 0, **kwargs: Any
    ) -> Any:
        """
        Given an application ID, return all Box names. No particular ordering is guaranteed. Request fails when client or server-side configured limits prevent returning all Box names.

        NOTE: box names are returned as base64-encoded strings.

        Args:
            application_id (int): The ID of the application to look up.
            limit (int, optional): Max number of box names to return.
                If max is not set, or max == 0, returns all box-names up to the maximum configured by the algod server being queried.
        """
        req = "/applications/" + str(application_id) + "/boxes"
        params = {"max": limit} if limit else {}
        return self.algod_request("GET", req, params=params, **kwargs)

    def account_asset_info(
        self, address: str, asset_id: int, **kwargs: Any
    ) -> Any:
        """
        Return asset information for a specific account.

        Args:
            address (str): account public key
            asset_id (int): The ID of the asset to look up.
        """
        query: Mapping = {}
        req = "/accounts/" + address + "/assets/" + str(asset_id)
        return self.algod_request("GET", req, query, **kwargs)

    def account_application_info(
        self, address: str, application_id: int, **kwargs: Any
    ) -> Any:
        """
        Return application information for a specific account.

        Args:
            address (str): account public key
            application_id (int): The ID of the application to look up.
        """
        query: Mapping = {}
        req = "/accounts/" + address + "/applications/" + str(application_id)
        return self.algod_request("GET", req, query, **kwargs)

    def pending_transactions_by_address(
        self,
        address: str,
        limit: int = 0,
        response_format: str = "json",
        **kwargs: Any
    ) -> Any:
        """
        Get the list of pending transactions by address, sorted by priority,
        in decreasing order, truncated at the end at MAX. If MAX = 0, returns
        all pending transactions.

        Args:
            address (str): account public key
            limit (int, optional): maximum number of transactions to return
            response_format (str): the format in which the response is returned: either
                "json" or "msgpack"
        """
        query: Dict[str, Union[str, int]] = {"format": response_format}
        if limit:
            query["max"] = limit
        req = "/accounts/" + address + "/transactions/pending"
        res = self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )
        return res

    def block_info(
        self,
        block: Optional[int] = None,
        response_format: str = "json",
        round_num: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """
        Get the block for the given round.

        Args:
            block (int): block number
            response_format (str): the format in which the response is
                returned: either "json" or "msgpack"
            round_num (int, optional): alias for block; specify one of these
        """
        query = {"format": response_format}
        if block is None and round_num is None:
            raise error.UnderspecifiedRoundError()
        req = "/blocks/" + _specify_round_string(block, round_num)
        res = self.algod_request(
            "GET", req, query, response_format=response_format, **kwargs
        )
        return res

    def ledger_supply(self, **kwargs: Any) -> Any:
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algod_request("GET", req, **kwargs)

    def status(self, **kwargs: Any) -> Any:
        """Return node status."""
        req = "/status"
        return self.algod_request("GET", req, **kwargs)

    def status_after_block(
        self,
        block_num: Optional[int] = None,
        round_num: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """
        Return node status immediately after blockNum.

        Args:
            block_num: block number
            round_num (int, optional): alias for block_num; specify one of
                these
        """
        if block_num is None and round_num is None:
            raise error.UnderspecifiedRoundError()
        req = "/status/wait-for-block-after/" + _specify_round_string(
            block_num, round_num
        )
        return self.algod_request("GET", req, **kwargs)

    def send_transaction(
        self, txn: "transaction.Transaction", **kwargs: Any
    ) -> Any:
        """
        Broadcast a signed transaction object to the network.

        Args:
            txn (SignedTransaction or MultisigTransaction): transaction to send
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        assert not isinstance(
            txn, transaction.Transaction
        ), "Attempt to send UNSUPPORTED type of transaction {}".format(txn)
        return self.send_raw_transaction(
            encoding.msgpack_encode(txn), **kwargs
        )

    def send_raw_transaction(
        self, txn: Union[bytes, str], **kwargs: Any
    ) -> Any:
        """
        Broadcast a signed transaction to the network.

        Args:
            txn (str): transaction to send, encoded in base64
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        txn_bytes = base64.b64decode(txn)
        req = "/transactions"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/x-binary"},
        )
        kwargs["headers"] = headers

        return self.algod_request("POST", req, data=txn_bytes, **kwargs)[
            "txId"
        ]

    def pending_transactions(
        self, max_txns: int = 0, response_format: str = "json", **kwargs: Any
    ) -> Any:
        """
        Return pending transactions.

        Args:
            max_txns (int): maximum number of transactions to return;
                if max_txns is 0, return all pending transactions
            response_format (str): the format in which the response is returned: either
                "json" or "msgpack"
        """
        query: Dict[str, Union[int, str]] = {"format": response_format}
        if max_txns:
            query["max"] = max_txns
        req = "/transactions/pending"
        res = self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )
        return res

    def pending_transaction_info(
        self, transaction_id: str, response_format: str = "json", **kwargs: Any
    ) -> Any:
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
            response_format (str): the format in which the response is returned: either
                "json" or "msgpack"
        """
        req = "/transactions/pending/" + transaction_id
        query = {"format": response_format}
        res = self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )
        return res

    def health(self, **kwargs: Any) -> Any:
        """Return null if the node is running."""
        req = "/health"
        return self.algod_request("GET", req, **kwargs)

    def versions(self, **kwargs: Any) -> Any:
        """Return algod versions."""
        req = "/versions"
        return self.algod_request("GET", req, **kwargs)

    def send_transactions(
        self,
        txns: "Iterable[transaction.GenericSignedTransaction]",
        **kwargs: Any
    ) -> Any:
        """
        Broadcast list of a signed transaction objects to the network.

        Args:
            txns (SignedTransaction[] or MultisigTransaction[]):
                transactions to send
            request_header (dict, optional): additional header for request

        Returns:
            str: first transaction ID
        """
        serialized: List[bytes] = []
        for txn in txns:
            assert not isinstance(
                txn, transaction.Transaction
            ), "Attempt to send UNSIGNED transaction {}".format(txn)
            serialized.append(base64.b64decode(encoding.msgpack_encode(txn)))

        return self.send_raw_transaction(
            base64.b64encode(b"".join(serialized)), **kwargs
        )

    def suggested_params(self, **kwargs: Any) -> Any:
        """Return suggested transaction parameters."""
        req = "/transactions/params"
        res = self.algod_request("GET", req, **kwargs)

        return transaction.SuggestedParams(
            res["fee"],
            res["last-round"],
            res["last-round"] + 1000,
            res["genesis-hash"],
            res["genesis-id"],
            False,
            res["consensus-version"],
            res["min-fee"],
        )

    def compile(
        self, source: str, source_map: bool = False, **kwargs: Any
    ) -> Any:
        """
        Compile TEAL source with remote algod.

        Args:
            source (str): source to be compiled
            request_header (dict, optional): additional header for request

        Returns:
            dict: loaded from json response body. "result" property contains compiled bytes, "hash" - program hash (escrow address)

        """
        req = "/teal/compile"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/x-binary"},
        )
        kwargs["headers"] = headers
        params = {"sourcemap": source_map}
        return self.algod_request(
            "POST", req, params=params, data=source.encode("utf-8"), **kwargs
        )

    def dryrun(self, drr: Dict[str, Any], **kwargs: Any) -> Any:
        """
        Dryrun with remote algod.

        Args:
            drr (obj): dryrun request object
            request_header (dict, optional): additional header for request

        Returns:
            dict: loaded from json response body
        """
        req = "/teal/dryrun"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/msgpack"},
        )
        kwargs["headers"] = headers
        data = encoding.msgpack_encode(drr)
        data = base64.b64decode(data)

        return self.algod_request("POST", req, data=data, **kwargs)

    def genesis(self, **kwargs: Any) -> Any:
        """Returns the entire genesis file."""
        req = "/genesis"
        return self.algod_request("GET", req, **kwargs)

    def transaction_proof(
        self,
        round_num: int,
        txid: str,
        hashtype: str = "",
        response_format: str = "json",
        **kwargs: Any
    ) -> Any:
        """
        Get a proof for a transaction in a block.

        Args:
            round_num (int): The round in which the transaction appears.
            txid (str): The transaction ID for which to generate a proof.
            hashtype (str): The type of hash function used to create the proof, must be either sha512_256 or sha256.
        """
        params = {"format": response_format}
        if hashtype != "":
            params["hashtype"] = hashtype
        req = "/blocks/{}/transactions/{}/proof".format(round_num, txid)
        return self.algod_request(
            "GET",
            req,
            params=params,
            response_format=response_format,
            **kwargs
        )

    def lightblockheader_proof(self, round_num: int, **kwargs: Any) -> Any:
        """
         Gets a proof for a given light block header inside a state proof commitment.

        Args:
            round_num (int): The round to which the light block header belongs.
        """
        req = "/blocks/{}/lightheader/proof".format(round_num)
        return self.algod_request("GET", req, **kwargs)

    def stateproofs(self, round_num: int, **kwargs: Any) -> Any:
        """
        Get a state proof that covers a given round

        Args:
            round_num (int): The round for which a state proof is desired.
        """
        req = "/stateproofs/{}".format(round_num)
        return self.algod_request("GET", req, **kwargs)

    def get_block_hash(self, round_num: int, **kwargs: Any) -> Any:
        """
        Get the block hash for the block on the given round.

        Args:
            round_num (int): The round in which the transaction appears.
        """
        req = "/blocks/{}/hash".format(round_num)
        return self.algod_request("GET", req, **kwargs)

    def simulate_transactions(
        self,
        txns: "Iterable[transaction.GenericSignedTransaction]",
        **kwargs: Any
    ) -> Any:
        """
        Simulate a list of a signed transaction objects being sent to the network.

        Args:
            txns (SignedTransaction[] or MultisigTransaction[]):
                transactions to send
            request_header (dict, optional): additional header for request

        Returns:
            Dict[str, Any]: results from simulation of transaction group
        """
        serialized = []
        for txn in txns:
            serialized.append(base64.b64decode(encoding.msgpack_encode(txn)))

        return self.simulate_raw_transaction(
            base64.b64encode(b"".join(serialized)), **kwargs
        )

    def simulate_raw_transaction(self, txn: bytes, **kwargs: Any) -> Any:
        """
        Simulate a transaction group

        Args:
            txn (str): transaction to send, encoded in base64
            request_header (dict, optional): additional header for request

        Returns:
            Dict[str, Any]: results from simulation of transaction group
        """
        txn = base64.b64decode(txn)
        req = "/transactions/simulate"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/x-binary"},
        )
        kwargs["headers"] = headers

        return self.algod_request("POST", req, data=txn, **kwargs)


def _specify_round_string(
    block: Optional[int], round_num: Optional[int]
) -> str:
    """
    Return the round number specified in either 'block' or 'round_num'.

    Args:
        block (int): user specified variable
        round_num (int): user specified variable
    """

    if not (block is None or round_num is None):
        raise error.OverspecifiedRoundError()

    if round_num:
        return str(block)

    return str(round_num)
