class WalletHandleResponse:
    """
    Attributes:
        expires_seconds (int): how long the handle is valid for
        wallet (WalletResponse): wallet information
    """
    def __init__(self, dictionary):
        wh = dictionary["wallet_handle"]
        self.expires_seconds = wh["expires_seconds"]
        self.wallet = WalletResponse(wh["wallet"])


class WalletResponse:
    """
    Attributes:
        driver_name (str)
        driver_version (int)
        id (str): wallet ID
        mnemonic_ux (bool)
        name (str): wallet name
        supported_txs (str[]): which transaction types are supported
    """
    def __init__(self, w):
        self.driver_name = w["driver_name"]
        self.driver_version = w["driver_version"]
        self.id = w["id"]
        self.mnemonic_ux = w["mnemonic_ux"]
        self.name = w["name"]
        self.supported_txs = w["supported_txs"]
