from algosdk import encoding, transaction


class BlockInfo:
    def __init__(self, block, cert):
        self.block = block
        self.cert = cert
        pass

    @staticmethod
    def undictify(d):
        return BlockInfo(
            encoding.undictify(d.get("block")),
            encoding.undictify(d.get("cert")),
        )

    def __str__(self):
        return (
            "{"
            + ", ".join(
                [
                    str(key) + ": " + str(value)
                    for key, value in self.__dict__.items()
                ]
            )
            + "}"
        )


class Block:
    def __init__(
        self,
        round,
        branch,
        seed,
        commit,
        sha256commit,
        timestamp,
        genesis_id,
        genesis_hash,
        counter,
        payset,
    ):
        self.round = round
        self.branch = branch
        self.seed = seed
        self.commit = commit
        self.sha256commit = sha256commit
        self.timestamp = timestamp
        self.genesis_id = genesis_id
        self.genesis_hash = genesis_hash
        self.counter = counter
        self.payset = payset

    @staticmethod
    def undictify(d):
        stxns = []
        gi = d.get("gen")
        gh = d.get("gh")
        for stib in d.get("txns", []):
            stxn = stib.copy()
            stxn["txn"] = stxn["txn"].copy()
            if stib.get("hgi", False):
                stxn["txn"]["gi"] = gi
            # Unconditionally put the genesis hash into the txn.  This
            # is not strictly correct for very early transactions
            # (v15) on testnet.  They could have been submitted
            # without genhash.
            stxn["txn"]["gh"] = gh
            stxns.append(transaction.SignedTxnWithAD.undictify(stxn))
        return Block(
            round=d.get("rnd", 0),
            branch=d.get("prev"),
            seed=d.get("seed"),
            commit=d.get("txn"),
            sha256commit=d.get("txn256"),
            timestamp=d.get("ts", 0),
            genesis_id=d.get("gen"),
            genesis_hash=d.get("gh"),
            counter=d.get("tc", 0),
            payset=stxns,
        )

    def __str__(self):
        return (
            "{"
            + ", ".join(
                [
                    str(key) + ": " + str(value)
                    for key, value in self.__dict__.items()
                ]
            )
            + "}"
        )


class Cert:
    def __init__(self):
        pass

    @staticmethod
    def undictify(d):
        return Cert()
