class WalletHandleResponse:
    """
    Attributes
    ----------
    expires_seconds: int
        how long the handle is valid for
    
    wallet: WalletResponse
        wallet information

    raw: dict
    """
    def __init__(self, dictionary):
        wh = dictionary["wallet_handle"]
        self.raw = wh
        self.expires_seconds = wh["expires_seconds"]
        self.wallet = WalletResponse(wh["wallet"])

class WalletResponse:
    """
    Attributes
    ----------
    driver_name: string

    driver_version: int

    id: string
        wallet ID

    mnemonic_ux: boolean

    name: string
        wallet name

    supported_txs: string[]

    raw: dict
    """
    def __init__(self, w):
        self.raw = w
        self.driver_name = w["driver_name"]
        self.driver_version = w["driver_version"]
        self.id = w["id"]
        self.mnemonic_ux = w["mnemonic_ux"]
        self.name = w["name"]
        self.supported_txs = w["supported_txs"]


