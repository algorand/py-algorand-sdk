import time
from . import constants


class Wallet:
    """
    Represents a wallet. If the wallet doesn't already exist, it will be created.
    
    Parameters
    ----------
    wallet_name: str

    wallet_pswd: str

    kmd_client: kmdClient
    """

    def __init__(self, wallet_name, wallet_pswd, kmd_client):
        self.name = wallet_name
        self.pswd = wallet_pswd
        self.kcl = kmd_client
        self.id = None
        
        # check if wallet already exists; if it does, set ID; if it doesn't, create
        wallets = self.kcl.listWallets()
        for w in wallets:
            if w.name.__eq__(self.name):
                self.id = w.id
        if not self.id:
            w = self.kcl.createWallet(self.name, self.pswd)
            self.id = w.id

        self.handle = self.kcl.initWalletHandle(self.id, self.pswd)
        self.last_handle_renew = time.time()

    def info(self):
        """Gets wallet information."""
        self.automateHandle()
        return self.kcl.getWallet(self.handle)

    def listKeys(self):
        """Lists the accounts in the wallet."""
        self.automateHandle()
        return self.kcl.listKeys(self.handle)

    def rename(self, new_name):
        """Renames the wallet."""
        resp = self.kcl.renameWallet(self.id, self.pswd, new_name)
        self.name = new_name
        return resp

    def exportMasterDerivationKey(self):
        """Returns the master derivation key."""
        self.automateHandle()
        return self.kcl.exportMasterDerivationKey(self.handle, self.pswd)
    
    def importKey(self, private_key):
        """Imports an account into the wallet."""
        self.automateHandle()
        return self.kcl.importKey(self.handle, private_key)

    def exportKey(self, address):
        """Returns the private key of the address."""
        self.automateHandle()
        return self.kcl.exportKey(self.handle, self.pswd, address)

    def generateKey(self):
        """Creates an account in the wallet."""
        self.automateHandle()
        return self.kcl.generateKey(self.handle)

    def deleteKey(self, address):
        """Deletes an account."""
        self.automateHandle()
        return self.kcl.deleteKey(self.handle, self.pswd, address)

    def signTransaction(self, txn):
        """Signs the transaction and returns a SignedTransaction object."""
        self.automateHandle()
        return self.kcl.signTransaction(self.handle, self.pswd, txn)

    def listMultisig(self):
        """Lists the multisig accounts in the wallet."""
        self.automateHandle()
        return self.kcl.listMultisig(self.handle)

    def importMultisig(self, multisig):
        """Imports a multisig account into the wallet."""
        self.automateHandle()
        return self.kcl.importMultisig(self.handle, multisig)

    def exportMultisig(self, address):
        """Returns a Multisig object."""
        self.automateHandle()
        return self.kcl.exportMultisig(self.handle, address)

    def deleteMultisig(self, address):
        """Deletes a multisig account."""
        self.automateHandle()
        return self.kcl.deleteMultisig(self.handle, self.pswd, address)

    def signMultisigTransaction(self, public_key, preStx):
        """Signs a multisig transaction."""
        self.automateHandle()
        return self.kcl.signMultisigTransaction(self.handle, self.pswd, public_key, preStx)

    def automateHandle(self):
        """Gets a new handle or renews the current one."""
        t = time.time()
        if t - self.last_handle_renew > 59:
            self.initHandle()
        else:
            self.renewHandle()

    def initHandle(self):
        """Gets a new handle."""
        self.handle = self.kcl.initWalletHandle(self.id, self.pswd)
        self.last_handle_renew = time.time()
        return True

    def renewHandle(self):
        """Renews the current handle."""
        resp = self.kcl.renewWalletHandle(self.handle)
        self.last_handle_renew = time.time()
        return resp

    def releaseHandle(self):
        """Deactivates the current handle."""
        resp = self.kcl.releaseWalletHandle(self.handle)
        self.handle = None
        self.last_handle_renew = time.time() - constants.handleRenewTime
        return resp


        


