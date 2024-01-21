from algosdk import encoding, transaction


class BlockInfo:
    def __init__(self, block, certificate):
        self.block = block
        self.certificate = certificate
        pass

    @staticmethod
    def undictify(d):
        return BlockInfo(
            block=Block.undictify(d.get("block")),
            certificate=Cert.undictify(d.get("cert")),
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
        fee_sink,
        rewards_pool,
        rewards_level,
        rewards_rate,
        rewards_residue,
        rewards_calculation_round,
        upgrade_propose,
        upgrade_delay,
        upgrade_approve,
        current_protocol,
        next_protocol,
        next_protocol_approvals,
        next_protocol_vote_before,
        next_protocol_switch_on,
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
        self.fee_sink = fee_sink
        self.rewards_pool = rewards_pool
        self.rewards_level = rewards_level
        self.rewards_rate = rewards_rate
        self.rewards_residue = rewards_residue
        self.rewards_calculation_round = rewards_calculation_round
        self.upgrade_propose = upgrade_propose
        self.upgrade_delay = upgrade_delay
        self.upgrade_approve = upgrade_approve
        self.current_protocol = current_protocol
        self.next_protocol = next_protocol
        self.next_protocol_approvals = next_protocol_approvals
        self.next_protocol_vote_before = next_protocol_vote_before
        self.next_protocol_switch_on = next_protocol_switch_on
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
            fee_sink=encoding.encode_address(d.get("fees")),
            rewards_pool=encoding.encode_address(d.get("rwd")),
            rewards_level=d.get("earn", 0),
            rewards_rate=d.get("rate", 0),
            rewards_residue=d.get("frac", 0),
            rewards_calculation_round=d.get("rwcalr", 0),
            upgrade_propose=d.get("upgradeprop"),
            upgrade_delay=d.get("upgradedelay", 0),
            upgrade_approve=d.get("upgradeyes", False),
            current_protocol=d.get("proto"),
            next_protocol=d.get("nextproto"),
            next_protocol_approvals=d.get("nextyes", 0),
            next_protocol_vote_before=d.get("nextbefore", 0),
            next_protocol_switch_on=d.get("nextswitch", 0),
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
    def __init__(
        self, round, period, step, proposal, votes, equivocation_votes
    ):
        self.round = round
        self.period = period
        self.step = step
        self.proposal = proposal
        self.votes = votes
        self.equivocation_votes = equivocation_votes

    @staticmethod
    def undictify(d):
        return Cert(
            round=d.get("rnd", 0),
            period=d.get("per", 0),
            step=d.get("step", 0),
            proposal=ProposalValue.undictify(d.get("prop")),
            votes=[],
            equivocation_votes=[],
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


class ProposalValue:
    def __init__(
        self, original_period, original_proposer, block_digest, encoding_digest
    ):
        self.original_period = original_period
        self.original_proposer = original_proposer
        self.block_digest = block_digest
        self.encoding_digest = encoding_digest

    @staticmethod
    def undictify(d):
        return ProposalValue(
            original_period=d.get("oper", 0),
            original_proposer=d.get("oprop"),
            block_digest=d.get("dig"),
            encoding_digest=d.get("encdig"),
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
