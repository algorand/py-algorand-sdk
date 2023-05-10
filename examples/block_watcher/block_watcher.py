from algosdk.v2client import algod
from algosdk import encoding
from algosdk import transaction
from typing import List, Dict, Union
import msgpack
import base64

# Mainnet Example
#token = ""
#host = "https://mainnet-api.algonode.cloud" # Mainnet

# Sandbox Example
token = "a" * 64
host = "http://localhost:4001"
client = algod.AlgodClient(token, host)


class SignedTxnWithAD:
    txn: Union[transaction.SignedTransaction, transaction.Transaction]
    ad: "ApplyData"

    @staticmethod
    def from_msgp(stxn, gh, gen) -> "SignedTxnWithAD":
        s = SignedTxnWithAD()
        s.txn = parse_signed_transaction_msgp(stxn, gh, gen)
        s.ad = ApplyData.from_msgp(stxn)
        return s


class ApplyData:
    closing_amount: int
    asset_closing_amount: int
    sender_rewards: int
    receiver_rewards: int
    close_rewards: int
    eval_delta: "EvalDelta"
    config_asset: int
    application_id: int

    def __init__(
        self,
        closing_amount=0,
        asset_closing_amount=0,
        sender_rewards=0,
        receiver_rewards=0,
        close_rewards=0,
        eval_delta=None,
        config_asset=0,
        application_id=0,
    ):
        self.closing_amount = closing_amount
        self.asset_closing_amount = asset_closing_amount
        self.sender_rewards = sender_rewards
        self.receiver_rewards = receiver_rewards
        self.close_rewards = close_rewards
        self.eval_delta = eval_delta
        self.config_asset = config_asset
        self.application_id = application_id

    @staticmethod
    def from_msgp(apply_data: dict) -> "ApplyData":
        ad = ApplyData()
        if b"ca" in apply_data:
            ad.closing_amount = apply_data[b"ca"]
        if b"aca" in apply_data:
            ad.asset_closing_amount = apply_data[b"aca"]
        if b"rs" in apply_data:
            ad.sender_rewards = apply_data[b"rs"]
        if b"rr" in apply_data:
            ad.receiver_rewards = apply_data[b"rr"]
        if b"rc" in apply_data:
            ad.close_rewards = apply_data[b"rc"]
        if b"caid" in apply_data:
            ad.config_asset = apply_data[b"caid"]
        if b"apid" in apply_data:
            ad.application_id = apply_data[b"apid"]
        if b"dt" in apply_data:
            ad.eval_delta = EvalDelta.from_msgp(apply_data[b"dt"])
        return ad


class EvalDelta:
    global_delta: List["StateDelta"] | None
    local_deltas: Dict[int, "StateDelta"] | None
    logs: List[str]
    inner_txns: List["SignedTxnWithAD"]

    def __init__(
        self,
        global_delta: List["StateDelta"] | None = None,
        local_deltas: Dict[int, "StateDelta"] | None = None,
        logs: List[str] = [],
        inner_txns: List["SignedTxnWithAD"] = [],
    ):
        self.global_delta = global_delta
        self.local_deltas = local_deltas
        self.logs = logs
        self.inner_txns = inner_txns

    @staticmethod
    def from_msgp(delta: dict) -> "EvalDelta":
        ed = EvalDelta()
        if b"gd" in delta:
            ed.global_delta = [
                StateDelta.from_msgp(delta[b"gd"][idx]) for idx in delta[b"gd"]
            ]
        if b"ld" in delta:
            ed.local_deltas = {
                k: StateDelta.from_msgp(v) for k, v in delta[b"ld"].items()
            }
        if b"lg" in delta:
            ed.logs = delta[b"lg"]
        if b"itx" in delta:
            ed.inner_txns = [
                SignedTxnWithAD.from_msgp(itxn, b"", "") for itxn in delta[b"itx"]
            ]
        return ed


class StateDelta:
    action: int
    bytes: bytes
    uint: int

    @staticmethod
    def from_msgp(state_delta: dict) -> "StateDelta":
        sd = StateDelta()
        if b"at" in state_delta:
            sd.action = state_delta[b"at"]
        if b"bs" in state_delta:
            sd.bytes = base64.b64encode(state_delta[b"bs"])
        if b"ui" in state_delta:
            sd.uint = state_delta[b"ui"]
        return sd


def parse_signed_transaction_msgp(
    txn: dict, gh: bytes, gen: str
) -> transaction.Transaction:
    stxn = {
        "txn": {
            "gh": gh,
            "gen": gen,
            **_stringify_keys(txn[b"txn"]),
        }
    }
    if b"sig" in txn:
        stxn["sig"] = txn[b"sig"]
    if b"msig" in txn:
        stxn["msig"] = _stringify_keys(txn[b"msig"])
        stxn["msig"]["subsig"] = [_stringify_keys(ss) for ss in stxn["msig"]["subsig"]]
    if b"lsig" in txn:
        stxn["lsig"] = _stringify_keys(txn[b"lsig"])
    if b"sgnr" in txn:
        stxn["sgnr"] = txn[b"sgnr"]
    return encoding.msgpack_decode(stxn)


def _stringify_keys(d: dict) -> dict:
    return {k.decode("utf-8"): v for (k, v) in d.items()}


def _txid_to_bytes(txid):
    return base64.b32decode(encoding._correct_padding(txid))


def _bytes_to_txid(b):
    return base64.b32encode(b).strip(b"=").decode("utf-8")


def get_itxn_id(
    itxn: transaction.Transaction, caller: transaction.Transaction, idx: int
) -> str:
    input = b"TX" + _txid_to_bytes(caller.get_txid())
    input += idx.to_bytes(8, "big")
    input += base64.b64decode(encoding.msgpack_encode(itxn))
    return _bytes_to_txid(encoding.checksum(input))


def print_ids_recursive(swad: SignedTxnWithAD, level: int):
    if swad.ad.eval_delta is None:
        return

    for idx in range(len(swad.ad.eval_delta.inner_txns)):
        itxn = swad.ad.eval_delta.inner_txns[idx]
        # These are Transactions not SignedTransactions
        print(
            "{} {}: {}".format(
                "\t" * (level + 1), itxn.txn.type, get_itxn_id(itxn.txn, swad.txn, idx)
            )
        )
        if itxn.ad.eval_delta is not None and len(itxn.ad.eval_delta.inner_txns) > 0:
            print_ids_recursive(itxn, level + 1)


if __name__ == "__main__":

    # Get current round
    round = client.status()['last-round']

    while (True):
        block = client.block_info(round, response_format="msgp")
        dblock = msgpack.unpackb(block, raw=True, strict_map_key=False)

        raw_block = dblock[b"block"]
        if b"txns" not in raw_block:
            round = client.status_after_block(round)['last-round']
            continue

        gh = raw_block[b"gh"]
        gen = raw_block[b"gen"].decode("utf-8")

        tx_count = len(raw_block[b"txns"])
        print(f"Round {round} had {tx_count} txns")

        # Construct SignedTransaction object and print TxIDs
        for stxn in raw_block[b"txns"]:
            swad = SignedTxnWithAD.from_msgp(stxn, gh, gen)
            print(swad.txn.get_txid())
        
        # Wait for next round
        round = client.status_after_block(round)['last-round']

