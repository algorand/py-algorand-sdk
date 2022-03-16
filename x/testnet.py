from algosdk.v2client.algod import AlgodClient
from algosdk.kmd import KMDClient
from algosdk.v2client.indexer import IndexerClient

DEVNET_TOKEN = "a" * 64
ALGOD_PORT = 60000
KMD_PORT = 60001
INDEXER_PORTS = range(59_996, 60_000)

LIVE_ALGOD: AlgodClient = None


def get_algod(force_retry: bool = False) -> AlgodClient:
    global LIVE_ALGOD
    try:
        if force_retry or not LIVE_ALGOD:
            algod = AlgodClient(DEVNET_TOKEN, f"http://localhost:{ALGOD_PORT}")
            assert algod.status(), "algod.status() did not produce any results"
            LIVE_ALGOD = algod
        return LIVE_ALGOD
    except Exception as e:
        LIVE_ALGOD = None
        raise Exception("algod is missing from environment") from e


def get_kmd() -> KMDClient:
    return KMDClient(DEVNET_TOKEN, f"http://localhost:{KMD_PORT}")


def get_indexer(port: int) -> IndexerClient:
    assert (
        port in INDEXER_PORTS
    ), f"port for available indexers must be in {INDEXER_PORTS} but was provided {port}"

    return IndexerClient(DEVNET_TOKEN, f"http://localhost:{port}")
