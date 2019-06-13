from urllib.request import Request, urlopen
from urllib import parse, error
import encoding
import urllib
import json

algodAuthHeader = "X-Algo-API-Token"
apiVersionPathPrefix = "/v1"
unversionedPaths = ["/health", "/versions", "/metrics"]
noAuth = ["/health"]


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
        """Executes a given request."""
        if requrl in noAuth:
            header = {}
        else:
            header = {
                algodAuthHeader: self.algodToken
                }

        if requrl not in unversionedPaths:
            requrl = apiVersionPathPrefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)
        if data:
            data = json.dumps(data, indent=2)
            data = bytearray(data, "ASCII")
        req = Request(self.algodAddress+requrl, headers=header, method=method, data=data)

        try:
            resp = urlopen(req)
        except error.HTTPError as e:
            return e.read().decode("ASCII")
        return json.loads(resp.read().decode("ASCII"))

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
            last = json.loads(self.status().decode("ASCII"))["lastRound"]
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
        """Broadcasts a signed transaction to the network."""
        query = {"rawtxn": signed_txn}
        req = "/transactions"
        return self.algodRequest("POST", req, data=query)

    def blockInfo(self, round):
        """Returns block information."""
        req = "/block/" + str(round)
        return self.algodRequest("GET", req)

if __name__ == "__main__":
    pass