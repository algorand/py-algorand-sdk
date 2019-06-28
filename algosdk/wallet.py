import time
from . import constants
from . import mnemonic


class Wallet:
    """
    Represents a wallet.

    Args:
        wallet_name (str): wallet name
        wallet_pswd (str): wallet password
        kmd_client (kmdClient): a kmdClient to handle wallet requests
        mdk (str, optional): master derivation key if recovering wallet

    Note:
        When initializing, if the wallet doesn't already exist, it will be
        created.

    Attributes:
        name (str)
        pswd (str)
        kcl (kmdClient)
        id (str)
        handle (str)
        last_handle_renew (float): time of last handle renew
    """

    def __init__(self, wallet_name, wallet_pswd, kmd_client, mdk=None):
        self.name = wallet_name
        self.pswd = wallet_pswd
        self.kcl = kmd_client
        self.id = None

        wallets = self.kcl.listWallets()
        for w in wallets:
            if w.name.__eq__(self.name):
                self.id = w.id
        if not self.id:
            w = self.kcl.createWallet(self.name, self.pswd,
                                      master_deriv_key=mdk)
            self.id = w.id
        self.last_handle_renew = time.time()
        self.handle = self.kcl.initWalletHandle(self.id, self.pswd)

    def info(self):
        """
        Get wallet information.

        Returns:
            WalletHandleResponse: object containing wallet handle information
                and wallet information
        """
        self.automateHandle()
        return self.kcl.getWallet(self.handle)

    def listKeys(self):
        """
        List all keys in the wallet.

        Returns:
            str[]: list of base32 addresses in the wallet
        """
        self.automateHandle()
        return self.kcl.listKeys(self.handle)

    def rename(self, new_name):
        """
        Rename the wallet.

        Args:
            new_name (str) : new name for the wallet

        Returns:
            WalletResponse: object containing wallet information
        """
        resp = self.kcl.renameWallet(self.id, self.pswd, new_name)
        self.name = new_name
        return resp

    def getRecoveryPhrase(self):
        """
        Get recovery phrase mnemonic for the wallet.

        Returns:
            str: mnemonic converted from the wallet's master derivation key
        """
        mdk = self.exportMasterDerivationKey()
        return mnemonic.fromMasterDerivationKey(mdk)

    def exportMasterDerivationKey(self):
        """
        Get the wallet's master derivation key.

        Returns:
            str: master derivation key
        """
        self.automateHandle()
        return self.kcl.exportMasterDerivationKey(self.handle, self.pswd)

    def importKey(self, private_key):
        """
        Import an account into a wallet.

        Args:
            private_key (str): private key of account to be imported

        Returns:
            str: base32 address of the account
        """
        self.automateHandle()
        return self.kcl.importKey(self.handle, private_key)

    def exportKey(self, address):
        """
        Return an account private key.

        Args:
            address (str): base32 address of the account

        Returns:
            str: private key
        """
        self.automateHandle()
        return self.kcl.exportKey(self.handle, self.pswd, address)

    def generateKey(self, display_mnemonic=True):
        """
        Generate a key in the wallet.

        Args:
            display_mnemonic (bool, optional): whether or not the mnemonic
                should be displayed

        Returns:
            str: base32 address of the generated account
        """
        self.automateHandle()
        return self.kcl.generateKey(self.handle)

    def deleteKey(self, address):
        """
        Delete a key in the wallet.

        Args:
            address (str): base32 address of account to be deleted

        Returns:
            bool: True if the account has been deleted
        """
        self.automateHandle()
        return self.kcl.deleteKey(self.handle, self.pswd, address)

    def signTransaction(self, txn):
        """
        Sign a transaction.

        Args:
            txn (Transaction): transaction to be signed

        Returns:
            SignedTransaction: signed transaction with signature of sender
        """
        self.automateHandle()
        return self.kcl.signTransaction(self.handle, self.pswd, txn)

    def listMultisig(self):
        """
        List all multisig accounts in the wallet.

        Returns:
            str[]: list of base32 multisig account addresses
        """
        self.automateHandle()
        return self.kcl.listMultisig(self.handle)

    def importMultisig(self, multisig):
        """
        Import a multisig account into the wallet.

        Args:
            multisig (Multisig): multisig account to be imported

        Returns:
            str: base32 address of the imported multisig account
        """
        self.automateHandle()
        return self.kcl.importMultisig(self.handle, multisig)

    def exportMultisig(self, address):
        """
        Export a multisig account.

        Args:
            address (str): base32 address of the multisig account

        Returns:
            Multisig: multisig object corresponding to the address
        """
        self.automateHandle()
        return self.kcl.exportMultisig(self.handle, address)

    def deleteMultisig(self, address):
        """
        Delete a multisig account.

        Args:
            address (str): base32 address of the multisig account to delete

        Returns:
            bool: True if the multisig account has been deleted
        """
        self.automateHandle()
        return self.kcl.deleteMultisig(self.handle, self.pswd, address)

    def signMultisigTransaction(self, public_key, preStx):
        """
        Sign a multisig transaction for the given public key.

        Args:
            public_key (str): base32 address that is signing the transaction
            preStx (SignedTransaction): object containing unsigned or
                partially signed multisig

        Returns:
            SignedTransaction: signed transaction with multisig containing
                public_key's signature
        """
        self.automateHandle()
        return self.kcl.signMultisigTransaction(self.handle, self.pswd,
                                                public_key, preStx)

    def automateHandle(self):
        """
        Get a new handle or renews the current one.

        Returns:
            bool: True if a handle is active
        """
        t = time.time()
        if t - self.last_handle_renew >= constants.handleRenewTime:
            self.initHandle()
        else:
            self.renewHandle()
        return True

    def initHandle(self):
        """
        Get a new handle.

        Returns:
            bool: True if a handle is active
        """
        self.last_handle_renew = time.time()
        self.handle = self.kcl.initWalletHandle(self.id, self.pswd)
        return True

    def renewHandle(self):
        """
        Renew the current handle.

        Returns:
            WalletHandleResponse: object containing wallet handle information
                and wallet information
        """
        self.last_handle_renew = time.time()
        resp = self.kcl.renewWalletHandle(self.handle)
        return resp

    def releaseHandle(self):
        """
        Deactivate the current handle.

        Returns:
            bool: True if the handle has been deactivated
        """
        resp = self.kcl.releaseWalletHandle(self.handle)
        self.handle = None
        self.last_handle_renew = time.time() - constants.handleRenewTime
        return resp
