from algosdk.v2client.algod import AlgodClient
from algosdk.kmd import KMDClient
from algosdk.v2client.indexer import IndexerClient

DEVNET_TOKEN = "a" * 64
ALGOD_PORT = 60000
KMD_PORT = 60001
INDEXER_PORTS = range(59_996, 60_000)


def get_algod() -> AlgodClient:
    return AlgodClient(DEVNET_TOKEN, f"http://localhost:{ALGOD_PORT}")


def get_kmd() -> KMDClient:
    return KMDClient(DEVNET_TOKEN, f"http://localhost:{KMD_PORT}")


def get_indexer(port: int) -> IndexerClient:
    assert (
        port in INDEXER_PORTS
    ), f"port for available indexers must be in {INDEXER_PORTS} but was provided {port}"

    return IndexerClient(DEVNET_TOKEN, f"http://localhost:{port}")
