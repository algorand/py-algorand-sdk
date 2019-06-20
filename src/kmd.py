from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import encoding
import error
import transaction
import base64
import responses

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
        dict: loaded from json response body 
        """
        if requrl in noAuth:
            header = {}
        else:
            header = {
                kmdAuthHeader: self.kmdToken
                }
        if requrl not in unversionedPaths:
            requrl = apiVersionPathPrefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)
        if data:
            data = json.dumps(data, indent=2)
            data = bytearray(data, "ascii")
        req = Request(
            self.kmdAddress+requrl, headers=header,
            method=method, data=data)
        resp = None
        try:
            resp = urlopen(req)
        except urllib.error.HTTPError as e:
            e = e.read().decode("ascii")
            try:
                raise error.KmdHTTPError(json.loads(e)["message"])
            except:
                raise error.KmdHTTPError(e)
        return json.loads(resp.read().decode("ascii"))

    def getVersion(self):
        """
        Gets kmd versions.
        
        Returns
        -------
        string[]: list of versions
        """
        req = "/versions"
        return self.kmdRequest("GET", req)["versions"]

    def listWallets(self):
        """
        Lists all wallets hosted on node.

        Returns
        -------
        WalletResponse[]: list of objects containing wallet information
        """
        req = "/wallets"
        result = self.kmdRequest("GET", req)["wallets"]
        return [responses.WalletResponse(w) for w in result]


    def createWallet(self, name, pswd, driver_name = "sqlite", master_deriv_key=None):
        """
        Creates a new wallet.

        Parameters
        ----------
        name: string
            wallet name
        
        pswd: string
            wallet password

        driver_name: string

        master_deriv_key: string
        
        Returns
        -------
        WalletResponse: object containing wallet information
        """
        req = "/wallet"
        query = {
            "wallet_driver_name": driver_name,
            "wallet_name": name,
            "wallet_password": pswd
            }
        if master_deriv_key:
            query["master_derivation_key"] = master_deriv_key
        result = self.kmdRequest("POST", req, data=query)["wallet"]
        return responses.WalletResponse(result)

    def getWallet(self, handle):
        """
        Gets wallet information.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        Returns
        -------
        WalletHandleResponse: object containing wallet handle information and wallet information
        
        """
        req = "/wallet/info"
        query = {"wallet_handle_token": handle}
        result = self.kmdRequest("POST", req, data=query)
        return responses.WalletHandleResponse(result)

    def initWalletHandle(self, id, password):
        """
        Initializes a handle for the wallet.
        
        Parameters
        ----------
        id: string
            wallet ID
        
        password: string
            wallet password

        Returns
        -------
        string: wallet handle token
        """
        req = "/wallet/init"
        query = {
            "wallet_id": id,
            "wallet_password": password
            }
        return self.kmdRequest("POST", req, data=query)["wallet_handle_token"]

    def releaseWalletHandle(self, handle):
        """
        Deactivates the handle for the wallet.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        Returns
        -------
        boolean: True if the handle has been deactivated
        """
        req = "/wallet/release"
        query = {"wallet_handle_token": handle}
        result = self.kmdRequest("POST", req, data=query)
        return result == {}

    def renewWalletHandle(self, handle):
        """
        Renews the wallet handle.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        Returns
        -------
        WalletHandleResponse: object containing wallet handle information and wallet information
        """
        req = "/wallet/renew"
        query = {
            "wallet_handle_token": handle
            }
        result = self.kmdRequest("POST", req, data=query)
        return responses.WalletHandleResponse(result)

    def renameWallet(self, id, password, new_name):
        """
        Renames the wallet.
        
        Parameters
        ----------
        id: string
            wallet ID

        password: string
            wallet password

        new_name: string

        Returns
        -------
        WalletResponse: object containing wallet information
        """
        req = "/wallet/rename"
        query = {
            "wallet_id": id,
            "wallet_password": password,
            "wallet_name": new_name
            }
        result = self.kmdRequest("POST", req, data=query)
        return responses.WalletResponse(result)

    def exportMasterDerivationKey(self, handle, password):
        """
        Gets the wallet's master derivation key.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        password: string
            wallet password
        """
        req = "/master-key/export"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password
            }
        return self.kmdRequest("POST", req, data=query)["master_derivation_key"]

    def importKey(self, handle, private_key):
        """
        Imports an account into a wallet.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        private_key: string

        Returns
        -------
        string: base32 address of the account
        """
        req = "/key/import"
        query = {
            "wallet_handle_token": handle,
            "private_key": private_key
            }
        return self.kmdRequest("POST", req, data=query)["address"]

    def exportKey(self, handle, password, address):
        """
        Returns an account private key.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        password: string
            wallet password

        address: string
            base32 address of the account
        
        Returns
        -------
        string: private key
        """
        req = "/key/export"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address
            }
        return self.kmdRequest("POST", req, data=query)["private_key"]

    def generateKey(self, handle, display_mnemonic=True):
        """
        Generates a key in the wallet.
        
        Parameters
        ----------
        handle: string
            wallet handle token
        
        display_mnemonic: boolean

        Returns
        -------
        string: base32 address of the generated account
        """
        req = "/key"
        query = {
            "wallet_handle_token": handle
            }
        return self.kmdRequest("POST", req, data=query)["address"]

    def deleteKey(self, handle, password, address):
        """
        Deletes a key in the wallet.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        password: string
            wallet password
        
        address: string
            base32 address of account to be deleted
        
        Returns
        -------
        boolean: True if the account has been deleted
        """
        req = "/key"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address
            }
        result = self.kmdRequest("DELETE", req, data=query)
        return result == {}

    def listKeys(self, handle):
        """
        Lists all keys in the wallet.

        Parameters
        ----------
        handle: string
            wallet handle token

        Returns
        -------
        string[]: list of base32 addresses in the wallet
        """
        req = "/key/list"
        query = {
            "wallet_handle_token": handle
            }
        return self.kmdRequest("POST", req, data=query)["addresses"]

    def signTransaction(self, handle, password, txn):
        """
        Signs a transaction.
        
        Parameters
        ----------
        handle: string
            wallet handle token
        
        password: string
            wallet password

        txn: Transaction

        Returns
        -------
        SignedTransaction
        """
        # transaction is a Transaction object
        txn = encoding.msgpack_encode(txn)
        req = "/transaction/sign"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "transaction": txn
            }
        result = self.kmdRequest("POST", req, data=query)["signed_transaction"]
        return encoding.msgpack_decode(result)

    def listMultisig(self, handle):
        """
        Lists all multisig accounts in the wallet.
        
        Parameters
        ----------
        handle: string
            wallet handle token
        
        Returns
        -------
        string[]: list of base32 multisig account addresses
        """
        req = "/multisig/list"
        query = {
            "wallet_handle_token": handle
            }
        result = self.kmdRequest("POST", req, data=query)
        if result == {}:
            return []
        return result["addresses"]

    def importMultisig(self, handle, multisig):
        """
        Imports a multisig account into the wallet.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        multisig: Multisig
            multisig account to be imported
        
        Returns
        -------
        string: base32 address of the imported multisig account
        """
        req = "/multisig/import"
        query = {
            "wallet_handle_token": handle,
            "multisig_version": multisig.version,
            "threshold": multisig.threshold,
            "pks": [base64.b64encode(s.public_key).decode() for s in multisig.subsigs]
            }
        return self.kmdRequest("POST", req, data=query)["address"]

    def exportMultisig(self, handle, address):
        """
        Exports a multisig account.

        Parameters
        ----------
        handle: string
            wallet token handle

        address: string
            base32 address of the multisig account

        Returns
        -------
        Multisig: multisig object corresponding to the address
        """
        req = "/multisig/export"
        query = {
            "wallet_handle_token": handle,
            "address": address
            }
        result = self.kmdRequest("POST", req, data=query)
        pks = result["pks"]
        pks = [encoding.encodeAddress(base64.b64decode(p)) for p in pks]
        msig = transaction.Multisig(result["multisig_version"], result["threshold"], pks)
        return msig

    def deleteMultisig(self, handle, password, address):
        """
        Deletes a multisig account.
        
        Parameters
        ----------
        handle: string
            wallet handle token

        password: string
            wallet password

        address: string
            base32 address of the multisig account to delete

        Returns
        -------
        boolean: True if the multisig account has been deleted
        """
        req = "/multisig"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "address": address
            }
        result = self.kmdRequest("DELETE", req, data=query)
        return result == {}


    def signMultisigTransaction(self, handle, password, public_key, preStx):
        """
        Signs a multisig transaction for the given public key.

        Parameters
        ----------
        handle: string
            wallet handle token
        
        password: string
            wallet password

        public_key: string
            base32 address that is signing the transaction

        preStx: SignedTransaction
            object containing unsigned or partially signed multisig
        
        Returns
        -------
        SignedTransaction
        """
        partial = preStx.multisig.json_dictify()
        txn = encoding.msgpack_encode(preStx.transaction)
        public_key = base64.b64encode(encoding.decodeAddress(public_key)).decode()
        
        req = "/multisig/sign"
        query = {
            "wallet_handle_token": handle,
            "wallet_password": password,
            "transaction": txn,
            "public_key": public_key,
            "partial_multisig": partial
            }
        result = self.kmdRequest("POST", req, data=query)["multisig"]
        msig = encoding.msgpack_decode(result)
        preStx.multisig = msig
        return preStx

if __name__ == "__main__":
    pass
