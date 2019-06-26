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
        algodToken (str): algod API token
        algodAddress (str): algod address

    Attributes:
        algodToken (str)
        algodAddress (str)
    """
    def __init__(self, algodToken, algodAddress):
        self.algodToken = algodToken
        self.algodAddress = algodAddress

    def algodRequest(self, method, requrl, params=None, data=None):
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
        if requrl in constants.noAuth:
            header = {}
        else:
            header = {
                constants.algodAuthHeader: self.algodToken
                }

        if requrl not in constants.unversionedPaths:
            requrl = constants.apiVersionPathPrefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)

        req = Request(self.algodAddress+requrl, headers=header, method=method,
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
        return self.algodRequest("GET", req)

    def health(self):
        """
        Return null if the node is running.
        """
        req = "/health"
        return self.algodRequest("GET", req)

    def statusAfterBlock(self, blockNum):
        """
        Return node status immediately after blockNum.

        Args:
            blockNum: block number
        """
        req = "/status/wait-for-block-after/" + str(blockNum)
        return self.algodRequest("GET", req)

    def pendingTransactions(self, maxTxns=0):
        """
        Return up to maxTxns pending transactions;

        Args:
            maxTxns (int): maximum number of transactions to return;
                if maxTxns is 0, return all pending transactions
        """
        query = {"max": maxTxns}
        req = "/transactions/pending"
        return self.algodRequest("GET", req, params=query)

    def versions(self):
        """Return algod versions."""
        req = "/versions"
        return self.algodRequest("GET", req)

    def ledgerSupply(self):
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algodRequest("GET", req)

    def transactionsByAddress(self, address, first=1, last=None, limit=0,
                              fromDate=None, toDate=None):
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
            fromDate (str, optional): no transactions before this date will be
                returned; format YYYY-MM-DD
            toDate (str, optional): no transactions after this date will be
                returned; format YYYY-MM-DD
        """
        if not last:
            last = self.status()["lastRound"]
        query = {"firstRound": first, "lastRound": last}
        if limit != 0:
            query["max"] = limit
        if toDate:
            query["toDate"] = toDate
        if fromDate:
            query["fromDate"] = fromDate
        req = "/account/" + address + "/transactions"
        return self.algodRequest("GET", req, params=query)

    def accountInfo(self, address):
        """
        Return account information.

        Args:
            address (str): account public key
        """
        req = "/account/" + address
        return self.algodRequest("GET", req)

    def transactionInfo(self, address, transaction_id):
        """
        Return transaction information.

        Args:
            address (str): account public key
            transaction_id (str): transaction ID
        """
        req = "/account/" + address + "/transaction/" + transaction_id
        return self.algodRequest("GET", req)

    def pendingTransactionInfo(self, transaction_id):
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transactions/pending/" + transaction_id
        return self.algodRequest("GET", req)

    def transactionByID(self, transaction_id):
        """
        Return transaction information; only works if indexer is enabled.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transaction/" + transaction_id
        return self.algodRequest("GET", req)

    def suggestedFee(self):
        """Return suggested transaction fee."""
        req = "/transactions/fee"
        return self.algodRequest("GET", req)

    def suggestedParams(self):
        """Return suggested transaction paramters."""
        req = "/transactions/params"
        return self.algodRequest("GET", req)

    def sendRawTransaction(self, signed_txn):
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
        return self.algodRequest("POST", req, data=signed_txn)["txId"]

    def blockInfo(self, round):
        """
        Return block information.

        Args:
            round (int): block number
        """
        req = "/block/" + str(round)
        return self.algodRequest("GET", req)

if __name__ == "__main__":
    pass
