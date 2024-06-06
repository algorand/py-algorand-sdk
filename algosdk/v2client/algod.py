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
    cast,
)
import urllib.error
from urllib import parse
from urllib.request import Request, urlopen

from algosdk import constants, encoding, error, transaction, util
from algosdk.v2client import models

AlgodResponseType = Union[Dict[str, Any], bytes]

# for compatibility with urllib.parse.urlencode
ParamsType = Union[Mapping[str, Any], Sequence[Tuple[str, Any]]]

api_version_path_prefix = "/v2"


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
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        response_format: Optional[str] = "json",
        timeout: Optional[int] = 30,
    ) -> AlgodResponseType:
        """
        Execute a given request.

        Args:
            method (str): request method
            requrl (str): url for the request
            params (ParamsType, optional): parameters for the request
            data (bytes, optional): data in the body of the request
            headers (dict, optional): additional header for request
            response_format (str, optional): format of the response
            timeout (int, optional): request timeout in seconds

        Returns:
            dict loaded from json response body when response_format == "json"
            otherwise returns the response body as bytes
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
            resp = urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            code = e.code
            es = e.read().decode("utf-8")
            m = e  # If json.loads() fails, we'll return e itself
            j = {}
            try:
                j = json.loads(es)
                m = j["message"]
            finally:
                raise error.AlgodHTTPError(m, code, j.get("data"))
        if response_format == "json":
            try:
                return json.load(resp)
            except Exception as e:
                # Some algod responses currently return a 200 OK
                # but have an empty response.
                # Do not return an error, and just return an empty response.
                if resp.status == 200 and resp.length == 0:
                    return {}
                raise error.AlgodResponseError(
                    "Failed to parse JSON response from algod"
                ) from e
        else:
            return resp.read()

    @classmethod
    def _assert_json_response(
        cls, params: Mapping[str, Any], endpoint: str = ""
    ) -> None:
        if params.get("response_format", "json") != "json":
            raise error.AlgodRequestError(
                f"Only json response is supported{ (' for ' + endpoint) if endpoint else ''}."
            )

    def account_info(
        self, address: str, exclude: Optional[str] = None, **kwargs: Any
    ) -> AlgodResponseType:
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

    def asset_info(self, asset_id: int, **kwargs: Any) -> AlgodResponseType:
        """
        Return information about a specific asset.

        Args:
            asset_id (int): The ID of the asset to look up.
        """
        req = "/assets/" + str(asset_id)
        return self.algod_request("GET", req, **kwargs)

    def application_info(
        self, application_id: int, **kwargs: Any
    ) -> AlgodResponseType:
        """
        Return information about a specific application.

        Args:
            application_id (int): The ID of the application to look up.
        """
        req = "/applications/" + str(application_id)
        return self.algod_request("GET", req, **kwargs)

    def application_box_by_name(
        self, application_id: int, box_name: bytes, **kwargs: Any
    ) -> AlgodResponseType:
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
    ) -> AlgodResponseType:
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
    ) -> AlgodResponseType:
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
    ) -> AlgodResponseType:
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
        **kwargs: Any,
    ) -> AlgodResponseType:
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
        **kwargs: Any,
    ) -> AlgodResponseType:
        """
        Get the block for the given round.

        Args:
            block (int): block number
            response_format (str): the format in which the response is
                returned: either "json" or "msgpack"
            round_num (int, optional): alias for block; specify one of these
        """
        query = {"format": response_format}
        req = "/blocks/" + _specify_round_string(block, round_num)
        res = self.algod_request(
            "GET", req, query, response_format=response_format, **kwargs
        )
        return res

    def ledger_supply(self, **kwargs: Any) -> AlgodResponseType:
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algod_request("GET", req, **kwargs)

    def status(self, **kwargs: Any) -> AlgodResponseType:
        """Return node status."""
        req = "/status"
        return self.algod_request("GET", req, **kwargs)

    def status_after_block(
        self,
        block_num: Optional[int] = None,
        round_num: Optional[int] = None,
        **kwargs: Any,
    ) -> AlgodResponseType:
        """
        Return node status immediately after blockNum.

        Args:
            block_num: block number
            round_num (int, optional): alias for block_num; specify one of
                these
        """
        req = "/status/wait-for-block-after/" + _specify_round_string(
            block_num, round_num
        )
        return self.algod_request("GET", req, **kwargs)

    def send_transaction(
        self, txn: "transaction.GenericSignedTransaction", **kwargs: Any
    ) -> str:
        """
        Broadcast a signed transaction object to the network.

        Args:
            txn (SignedTransaction, LogicSigTransaction, or MultisigTransaction): transaction to send
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
    ) -> str:
        """
        Broadcast a signed transaction to the network.

        Args:
            txn (str): transaction to send, encoded in base64
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        self._assert_json_response(kwargs, "send_raw_transaction")

        txn_bytes = base64.b64decode(txn)
        req = "/transactions"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/x-binary"},
        )
        kwargs["headers"] = headers

        resp = self.algod_request("POST", req, data=txn_bytes, **kwargs)
        return cast(str, cast(dict, resp)["txId"])

    def pending_transactions(
        self, max_txns: int = 0, response_format: str = "json", **kwargs: Any
    ) -> AlgodResponseType:
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
        return self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )

    def pending_transaction_info(
        self, transaction_id: str, response_format: str = "json", **kwargs: Any
    ) -> AlgodResponseType:
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
            response_format (str): the format in which the response is returned: either
                "json" or "msgpack"
        """
        req = "/transactions/pending/" + transaction_id
        query = {"format": response_format}
        return self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )

    def health(self, **kwargs: Any) -> AlgodResponseType:
        """Return null if the node is running."""
        req = "/health"
        return self.algod_request("GET", req, **kwargs)

    def versions(self, **kwargs: Any) -> AlgodResponseType:
        """Return algod versions."""
        req = "/versions"
        return self.algod_request("GET", req, **kwargs)

    def send_transactions(
        self,
        txns: "Iterable[transaction.GenericSignedTransaction]",
        **kwargs: Any,
    ) -> str:
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

    def suggested_params(self, **kwargs: Any) -> "transaction.SuggestedParams":
        """Return suggested transaction parameters."""
        self._assert_json_response(kwargs, "suggested_params")

        req = "/transactions/params"
        res = cast(dict, self.algod_request("GET", req, **kwargs))

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
    ) -> Dict[str, Any]:
        """
        Compile TEAL source with remote algod.

        Args:
            source (str): source to be compiled
            request_header (dict, optional): additional header for request

        Returns:
            dict: loaded from json response body. "result" property contains compiled bytes, "hash" - program hash (escrow address)
        """
        self._assert_json_response(kwargs, "compile")

        req = "/teal/compile"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/x-binary"},
        )
        kwargs["headers"] = headers
        params = {"sourcemap": source_map}
        return cast(
            Dict[str, Any],
            self.algod_request(
                "POST",
                req,
                params=params,
                data=source.encode("utf-8"),
                **kwargs,
            ),
        )

    def disassemble(
        self, program_bytes: bytes, **kwargs: Any
    ) -> Dict[str, str]:
        """
        Disassable TEAL program bytes with remote algod.
        Args:
            program (bytes): bytecode to be disassembled
            request_header (dict, optional): additional header for request
        Returns:
            dict: response dictionary containing disassembled TEAL source code
            in plain text as the value of the unique "result" key.
        """
        if not isinstance(program_bytes, bytes):
            raise error.InvalidProgram(
                message=f"disassemble endpoints only accepts bytes but request program_bytes is of type {type(program_bytes)}"
            )
        self._assert_json_response(kwargs, "disassemble")

        req = "/teal/disassemble"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/x-binary"},
        )
        kwargs["headers"] = headers
        return cast(
            Dict[str, str],
            self.algod_request("POST", req, data=program_bytes, **kwargs),
        )

    def dryrun(self, drr: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Dryrun with remote algod.

        Args:
            drr (obj): dryrun request object
            request_header (dict, optional): additional header for request

        Returns:
            dict: loaded from json response body
        """
        self._assert_json_response(kwargs, "dryrun")

        req = "/teal/dryrun"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/msgpack"},
        )
        kwargs["headers"] = headers
        data = encoding.msgpack_encode(drr)
        data = base64.b64decode(data)

        return cast(dict, self.algod_request("POST", req, data=data, **kwargs))

    def genesis(self, **kwargs: Any) -> AlgodResponseType:
        """Returns the entire genesis file."""
        req = "/genesis"
        return self.algod_request("GET", req, **kwargs)

    def transaction_proof(
        self,
        round_num: int,
        txid: str,
        hashtype: str = "",
        response_format: str = "json",
        **kwargs: Any,
    ) -> AlgodResponseType:
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
            **kwargs,
        )

    def lightblockheader_proof(
        self, round_num: int, **kwargs: Any
    ) -> AlgodResponseType:
        """
        Gets a proof for a given light block header inside a state proof commitment.

        Args:
            round_num (int): The round to which the light block header belongs.
        """
        req = "/blocks/{}/lightheader/proof".format(round_num)
        return self.algod_request("GET", req, **kwargs)

    def stateproofs(self, round_num: int, **kwargs: Any) -> AlgodResponseType:
        """
        Get a state proof that covers a given round

        Args:
            round_num (int): The round for which a state proof is desired.
        """
        req = "/stateproofs/{}".format(round_num)
        return self.algod_request("GET", req, **kwargs)

    def get_block_hash(
        self, round_num: int, **kwargs: Any
    ) -> AlgodResponseType:
        """
        Get the block hash for the block on the given round.

        Args:
            round_num (int): The round in which the transaction appears.
        """
        req = "/blocks/{}/hash".format(round_num)
        return self.algod_request("GET", req, **kwargs)

    def simulate_transactions(
        self,
        request: models.SimulateRequest,
        **kwargs: Any,
    ) -> AlgodResponseType:
        """
        Simulate transactions being sent to the network.

        Args:
            request (models.SimulateRequest): Simulation request object
            headers (dict, optional): additional header for request

        Returns:
            Dict[str, Any]: results from simulation of transactions
        """
        body = base64.b64decode(encoding.msgpack_encode(request))
        req = "/transactions/simulate"
        headers = util.build_headers_from(
            kwargs.get("headers", False),
            {"Content-Type": "application/msgpack"},
        )
        kwargs["headers"] = headers
        return self.algod_request("POST", req, data=body, **kwargs)

    def simulate_raw_transactions(
        self, txns: "Sequence[transaction.GenericSignedTransaction]", **kwargs
    ):
        """
        Simulate a transaction group being sent to the network.

        Args:
            txns (Sequence[transaction.GenericSignedTransaction]): transaction group to simulate
            headers (dict, optional): additional header for request

        Returns:
            Dict[str, Any]: results from simulation of transactions
        """
        request = models.SimulateRequest(
            txn_groups=[
                models.SimulateRequestTransactionGroup(txns=list(txns))
            ]
        )
        return self.simulate_transactions(request, **kwargs)

    def get_sync_round(self, **kwargs: Any) -> AlgodResponseType:
        """
        Get the minimum sync round for the ledger.

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = "/ledger/sync"
        return self.algod_request("GET", req, **kwargs)

    def set_sync_round(self, round: int, **kwargs: Any) -> AlgodResponseType:
        """
        Set the minimum sync round for the ledger.

        Args:
            round (int): Sync round

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = f"/ledger/sync/{round}"
        return self.algod_request("POST", req, **kwargs)

    def unset_sync_round(self, **kwargs: Any) -> AlgodResponseType:
        """
        Unset the minimum sync round for the ledger.

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = "/ledger/sync"
        return self.algod_request("DELETE", req, **kwargs)

    def ready(self, **kwargs: Any) -> AlgodResponseType:
        """
        Returns OK if the node is healthy and fully caught up.

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = "/ready"
        return self.algod_request("GET", req, **kwargs)

    def get_timestamp_offset(self, **kwargs: Any) -> AlgodResponseType:
        """
        Get the timestamp offset in block headers.
        This feature is only available in dev mode networks.

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = "/devmode/blocks/offset"
        return self.algod_request("GET", req, **kwargs)

    def set_timestamp_offset(
        self,
        offset: int,
        **kwargs: Any,
    ) -> AlgodResponseType:
        """
        Set the timestamp offset in block headers.
        This feature is only available in dev mode networks.

        Args:
            offset (int): Block timestamp offset

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = f"/devmode/blocks/offset/{offset}"
        return self.algod_request("POST", req, **kwargs)

    def get_ledger_state_delta(
        self, round: int, response_format: str = "json", **kwargs: Any
    ) -> AlgodResponseType:
        """
        Get the ledger state delta for a round.

        Args:
            round (int): The round for the desired state delta
            response_format (str): The format in which the response is returned: either
                "json" or "msgpack"

        Returns:
            Dict[str, Any]: Response from algod
        """
        query = {"format": response_format}
        req = f"/deltas/{round}"
        return self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )

    def get_transaction_group_ledger_state_deltas_for_round(
        self, round: int, response_format: str = "json", **kwargs: Any
    ) -> AlgodResponseType:
        """
        Get the ledger state deltas for all transaction groups in a given round.

        Args:
            round (int): The round for the desired state delta
            response_format (str): The format in which the response is returned: either
                "json" or "msgpack"

        Returns:
            Dict[str, Any]: Response from algod
        """
        query = {"format": response_format}
        req = f"/deltas/{round}/txn/group"
        return self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )

    def get_ledger_state_delta_for_transaction_group(
        self, id: str, response_format: str = "json", **kwargs: Any
    ) -> AlgodResponseType:
        """
        Get the ledger state delta for a transaction group given the
        transaction or group ID.

        Args:
            id (str): A transaction ID or transaction group ID
            response_format (str): The format in which the response is returned: either
                "json" or "msgpack"

        Returns:
            Dict[str, Any]: Response from algod
        """
        query = {"format": response_format}
        req = f"/deltas/txn/group/{id}"
        return self.algod_request(
            "GET", req, params=query, response_format=response_format, **kwargs
        )

    def get_block_txids(
        self, round_num: int, **kwargs: Any
    ) -> AlgodResponseType:
        """
        Get the top level transaction IDs for the block
        on the given round.

        Args:
            round_num (int): The round in which the transaction appears.

        Returns:
            Dict[str, Any]: Response from algod
        """
        req = "/blocks/{}/txids".format(round_num)
        return self.algod_request("GET", req, **kwargs)


def _specify_round_string(
    block: Union[int, None], round_num: Union[int, None]
) -> str:
    """
    Return the round number specified in either 'block' or 'round_num'.

    Args:
        block (int): user specified variable
        round_num (int): user specified variable
    """
    if block is None and round_num is None:
        raise error.UnderspecifiedRoundError()

    if block is not None and round_num is not None:
        raise error.OverspecifiedRoundError()

    if round_num is not None:
        return str(round_num)

    return str(block)
