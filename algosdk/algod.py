from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import base64
from . import error
from . import encoding
from . import constants


class AlgodClient:
    """Client class for kmd. Handles all kmd requests.

    Parameters
    ----------
    algodToken: string
        see algod.token
    algodAddress: string
        see algod.net
    """
    def __init__(self, algodToken, algodAddress):
        self.algodToken = algodToken
        self.algodAddress = algodAddress

    def algodRequest(self, method, requrl, params=None, data=None):
        """
        Executes a given request.
        
        Parameters
        ----------
        method: string

        requrl: string
        
        params: dict

        data: dict

        Returns
        -------
        dict: loaded from json response body """
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
            
        req = Request(self.algodAddress+requrl, headers=header, method=method, data=data)

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
        """Returns node status"""
        req = "/status"
        return self.algodRequest("GET", req)

    def health(self):
        """If the node is running, returns null"""
        req = "/health"
        return self.algodRequest("GET", req)

    def statusAfterBlock(self, blockNum):
        """Returns node status immediately after blockNum."""
        req = "/status/wait-for-block-after/" + str(blockNum)
        return self.algodRequest("GET", req)

    def pendingTransactions(self, maxTxns=0):
        """Returns up to maxTxns pending transactions; if maxTxns is 0,
        returns all pending transactions."""
        query = {"max": maxTxns}
        req = "/transactions/pending"
        return self.algodRequest("GET", req, params=query)

    def versions(self):
        """Returns algod versions."""
        req = "/versions"
        return self.algodRequest("GET", req)

    def ledgerSupply(self):
        """Returns supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algodRequest("GET", req)

    # need to make sure to stay within current block if not archival node
    # can only specify by date when indexer is enabled
    # maybe split into several functions depending on situation
    def transactionsByAddress(self, address, first=1, last=None, limit=0, fromDate=None, toDate=None):
        """Returns transactions for an address."""
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
        """Returns account information."""
        req = "/account/" + address
        return self.algodRequest("GET", req)

    def transactionInfo(self, address, transaction_id):
        """Returns transaction information."""
        req = "/account/" + address + "/transaction/" + transaction_id
        return self.algodRequest("GET", req)

    def pendingTransactionInfo(self, transaction_id):
        """Returns transaction information for a pending transaction."""
        req = "/transactions/pending/" + transaction_id
        return self.algodRequest("GET", req)

    def transactionByID(self, transaction_id):
        """Returns transaction information given its ID."""
        req = "/transaction/" + transaction_id
        return self.algodRequest("GET", req)

    def suggestedFee(self):
        """Returns suggested transaction fee."""
        req = "/transactions/fee"
        return self.algodRequest("GET", req)

    def suggestedParams(self):
        """Returns suggested transaction paramters."""
        req = "/transactions/params"
        return self.algodRequest("GET", req)

    def sendRawTransaction(self, signed_txn):
        """
        Broadcasts a signed transaction object to the network.
        
        Parameters
        ----------
        signed_txn: SignedTransaction

        Returns
        -------
        string: transaction ID
        """
        signed_txn = encoding.msgpack_encode(signed_txn)
        signed_txn = base64.b64decode(signed_txn)
        req = "/transactions"
        return self.algodRequest("POST", req, data=signed_txn)["txId"]

    def blockInfo(self, round):
        """Returns block information."""
        req = "/block/" + str(round)
        return self.algodRequest("GET", req)

if __name__ == "__main__":
    pass