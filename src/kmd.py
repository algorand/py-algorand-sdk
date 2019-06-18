from urllib.request import Request, urlopen
from urllib import parse, error
import json
import encoding


kmdAuthHeader = "X-KMD-API-Token"
apiVersionPathPrefix = "/v1"
unversionedPaths = ["/health", "/versions", "/metrics"]
noAuth = ["/health"]


class kmdClient:
    """Client class for kmd. Handles all kmd requests.

    Parameters
    ----------
    kmdToken: string
        see kmd.token
    kmdAddress: string
        see kmd.net
    """
    def __init__(self, kmdToken, kmdAddress):
        self.kmdToken = kmdToken
        self.kmdAddress = kmdAddress

    def kmdRequest(self, method, requrl, params=None, data=None):
        """Executes a given request."""
        if requrl in noAuth:
            header = {}
        else:
            header = {
                kmdAuthHeader: self.kmdToken,
                "Content-type": "application/json; charset=utf-8"
                }
        if requrl not in unversionedPaths:
            requrl = apiVersionPathPrefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)
        if data:
            data = json.dumps(data, indent=2)
            data = bytearray(data, "ASCII")
        req = Request(
            self.kmdAddress+requrl, headers=header,
            method=method, data=data)
        resp = None
        try:
            resp = urlopen(req)
        except error.HTTPError as e:
            return json.loads(e.read().decode("ASCII"))
        return json.loads(resp.read().decode("ASCII"))

    def getVersion(self):
        """Returns kmd versions."""
        req = "/versions"
        return self.kmdRequest("GET", req)

    def listWallets(self):
        """Returns wallets hosted on node."""
        req = "/wallets"
        return self.kmdRequest("GET", req)

    def createWallet(self, name, pswd, driver_name, master_deriv_key=None):
        """Creates a new wallet.
        Returns wallet information or error if wallet already exists."""
        req = "/wallet"
        query = {
            "wallet_driver_name": driver_name,
            "wallet_name": name,
            "wallet_password": pswd
            }
        if master_deriv_key:
            query["master_derivation_key"] = master_deriv_key
        return self.kmdRequest("POST", req, data=query)

    def getWallet(self, handle):
        """Returns wallet information."""
        req = "/wallet/info"
        query = {"wallet_handle_token": handle}
        return self.kmdRequest("POST", req, data=query)

    def initWalletHandle(self, id, password):
        """Returns a handle for the wallet."""
        req = "/wallet/init"
        query = {
            "wallet_id": id,
            "wallet_password": password
            }
        return self.kmdRequest("POST", req, data=query)

    def releaseWalletHandle(self, handle):
        """Deactivates the handle for the wallet."""
        req = "/wallet/release"
        query = {"wallet_handle_token": handle}
        return self.kmdRequest("POST", req, data=query)

    def renewWalletHandle(self, handle):
        """Renews the wallet handle; pushes back its expiration."""
        req = "/wallet/renew"
        query = {
            "wallet_handle_token": handle
            }
        return self.kmdRequest("POST", req, data=query)

    def renameWallet(self, id, password, new_name):
        """Renames the wallet."""
        req = "/wallet/rename"
        query = {
            "wallet_id": id,
            "wallet_password": password,
            "wallet_name": new_name
            }
        return self.kmdRequest("POST", req, data=query)

    def exportMasterDerivationKey(self, handle, password):
        """Returns the wallet's master derivation key."""
        req = "/master-key/export"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password
            }
        return self.kmdRequest("POST", req, data=query)

    def importKey(self, handle, secret_key):
        """Imports an account into a wallet."""
        req = "/key/import"
        query = {
            "wallet_handle_token": handle,
            "private_key": secret_key
            }
        return self.kmdRequest("POST", req, data=query)

    def exportKey(self, handle, password, address):
        """Returns an account private signing key."""
        req = "/key/export"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address
            }
        return self.kmdRequest("POST", req, data=query)

    def generateKey(self, handle, display_mnemonic):
        """Generates a key in the wallet."""
        req = "/key"
        query = {
            "wallet_handle_token": handle
            }
        return self.kmdRequest("POST", req, data=query)

    def deleteKey(self, handle, password, address):
        """Deletes a key in the wallet."""
        req = "/key"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address
            }
        return self.kmdRequest("DELETE", req, data=query)

    def listKeys(self, handle):
        """Returns all keys in the wallet."""
        req = "/key/list"
        query = {
            "wallet_handle_token": handle
            }
        return self.kmdRequest("POST", req, data=query)

    def signTransaction(self, handle, password, transaction):
        """Given a transaction, returns a signed transaction."""
        # transaction is a Transaction object
        txn = encoding.msgpack_encode(transaction)
        req = "/transaction/sign"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "transaction": txn
            }
        return self.kmdRequest("POST", req, data=query)

    def listMultisig(self, handle):
        """Returns all multisig accounts."""
        req = "/multisig/list"
        query = {
            "wallet_handle_token": handle
            }
        return self.kmdRequest("POST", req, data=query)

    def importMultisig(self, handle, version, threshold, public_keys):
        """Imports a multisig account into the wallet.
        public_keys are in base64
        """
        req = "/multisig/import"
        query = {
            "wallet_handle_token": handle,
            "multisig_version": version,
            "threshold": threshold,
            "pks": public_keys
            }
        return self.kmdRequest("POST", req, data=query)

    def exportMultisig(self, handle, address):
        """Returns a multisig preimage, containing
        public keys, version, and threshold.
        address is base32
        """
        req = "/multisig/export"
        query = {
            "wallet_handle_token": handle,
            "address": address
            }
        return self.kmdRequest("POST", req, data=query)

    def signMultisigTransaction(self, handle, password, transaction, public_key, partial):
        """Given a public key, returns a signed multisig transaction.
        transaction is obj
        public key is in base64
        multisig (partial) is obj
        """
        partial = partial.json_dictify()
        transaction = encoding.msgpack_encode(transaction)
        req = "/multisig/sign"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "transaction": transaction,
            "public_key": public_key,
            "partial_multisig": partial
            }
        return self.kmdRequest("POST", req, data=query)

if __name__ == "__main__":
    pass
