import base64
import msgpack
from collections import OrderedDict
from . import error
from . import encoding
from . import constants
from . import account
from nacl.signing import SigningKey


class Transaction:
    """
    Superclass for various transaction types.
    """
    def __init__(self, sender, fee, first, last, note, gen, gh):
        self.sender = sender
        self.fee = fee
        self.first_valid_round = first
        self.last_valid_round = last
        self.note = note
        self.genesis_id = gen
        self.genesis_hash = gh

        self.group = None

    def get_txid(self):
        """
        Get the transaction's ID.

        Returns:
            str: transaction ID
        """
        txn = encoding.msgpack_encode(self)
        to_sign = constants.txid_prefix + base64.b64decode(txn)
        txid = encoding.checksum(to_sign)
        txid = base64.b32encode(txid).decode()
        return encoding._undo_padding(txid)

    def sign(self, private_key):
        """
        Sign the transaction with a private key.

        Args:
            private_key (str): the private key of the signing account

        Returns:
            SignedTransaction: signed transaction with the signature
        """
        sig = self.raw_sign(private_key)
        sig = base64.b64encode(sig).decode()
        stx = SignedTransaction(self, sig)
        return stx

    def raw_sign(self, private_key):
        """
        Sign the transaction.

        Args:
            private_key (str): the private key of the signing account

        Returns:
            bytes: signature
        """
        private_key = base64.b64decode(private_key)
        txn = encoding.msgpack_encode(self)
        to_sign = constants.txid_prefix + base64.b64decode(txn)
        signing_key = SigningKey(private_key[:constants.signing_key_len_bytes])
        signed = signing_key.sign(to_sign)
        sig = signed.signature
        return sig

    def estimate_size(self):
        sk, _ = account.generate_account()
        stx = self.sign(sk)
        return len(base64.b64decode(encoding.msgpack_encode(stx)))

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        return (self.sender == other.sender and
                self.fee == other.fee and
                self.first_valid_round == other.first_valid_round and
                self.last_valid_round == other.last_valid_round and
                self.genesis_hash == other.genesis_hash and
                self.genesis_id == other.genesis_id and
                self.note == other.note)


class PaymentTxn(Transaction):
    """
    Represents a payment transaction.

    Args:
        sender (str): address of the sender
        fee (int): transaction fee (per byte if flat_fee is false)
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesis_hash
        receiver (str): address of the receiver
        amt (int): amount in microAlgos to be sent
        close_remainder_to (str, optional): if nonempty, account will be closed
            and remaining algos will be sent to this address
        note (bytes, optional): arbitrary optional bytes
        gen (str, optional): genesis_id
        flat_fee (bool): whether the specified fee is a flat fee

    Attributes:
        sender (str)
        fee (int)
        first_valid_round (int)
        last_valid_round (int)
        note (bytes)
        genesis_id (str)
        genesis_hash (str)
        group(bytes)
        receiver (str)
        amt (int)
        close_remainder_to (str)
        type (str)
    """

    def __init__(self, sender, fee, first, last, gh, receiver, amt,
                 close_remainder_to=None, note=None, gen=None, flat_fee=False):
        Transaction.__init__(self,  sender, fee, first, last, note, gen, gh)
        self.receiver = receiver
        self.amt = amt
        self.close_remainder_to = close_remainder_to
        self.type = constants.payment_txn
        if flat_fee:
            self.fee = max(constants.min_txn_fee, self.fee)
        else:
            self.fee = max(self.estimate_size()*self.fee,
                           constants.min_txn_fee)

    def dictify(self):
        od = OrderedDict()
        if self.amt:
            od["amt"] = self.amt
        if self.close_remainder_to:
            od["close"] = encoding.decode_address(self.close_remainder_to)
        od["fee"] = self.fee
        od["fv"] = self.first_valid_round
        if self.genesis_id:
            od["gen"] = self.genesis_id
        od["gh"] = base64.b64decode(self.genesis_hash)
        if self.group:
            od["grp"] = self.group
        od["lv"] = self.last_valid_round
        if self.note:
            od["note"] = self.note
        od["rcv"] = encoding.decode_address(self.receiver)
        od["snd"] = encoding.decode_address(self.sender)
        od["type"] = self.type

        return od

    @staticmethod
    def undictify(d):
        crt = None
        note = None
        gen = None
        amt = 0
        fv = 0
        grp = None
        if "close" in d:
            crt = encoding.encode_address(d["close"])
        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        if "amt" in d:
            amt = d["amt"]
        if "fv" in d:
            fv = d["fv"]
        if "grp" in d:
            grp = d["grp"]
        tr = PaymentTxn(encoding.encode_address(d["snd"]), d["fee"], fv,
                        d["lv"], base64.b64encode(d["gh"]).decode(),
                        encoding.encode_address(d["rcv"]), amt,
                        crt, note, gen, True)
        tr.group = grp
        return tr

    def __eq__(self, other):
        if not isinstance(other, PaymentTxn):
            return False
        return (super(PaymentTxn, self).__eq__(other) and
                self.receiver == other.receiver and
                self.amt == other.amt and
                self.close_remainder_to == other.close_remainder_to and
                self.type == other.type)


class KeyregTxn(Transaction):
    """
    Represents a key registration transaction.

    Args:
        sender (str): address of sender
        fee (int): transaction fee (per byte if flat_fee is false)
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesis_hash
        votekey (str): participation public key
        selkey (str): VRF public key
        votefst (int): first round to vote
        votelst (int): last round to vote
        votekd (int): vote key dilution
        note (bytes, optional): arbitrary optional bytes
        gen (str): genesis_id
        flat_fee (bool): whether the specified fee is a flat fee

    Attributes:
        sender (str)
        fee (int)
        first_valid_round (int)
        last_valid_round (int)
        note (bytes)
        genesis_id (str)
        genesis_hash (str)
        group(bytes)
        votepk (str)
        selkey (str)
        votefst (int)
        votelst (int)
        votekd (int)
        type (str)
    """

    def __init__(self, sender, fee, first, last, gh, votekey, selkey, votefst,
                 votelst, votekd, note=None, gen=None, flat_fee=False):
        Transaction.__init__(self, sender, fee, first, last, note, gen, gh)
        self.votepk = votekey
        self.selkey = selkey
        self.votefst = votefst
        self.votelst = votelst
        self.votekd = votekd
        self.type = constants.keyreg_txn
        if flat_fee:
            self.fee = max(constants.min_txn_fee, self.fee)
        else:
            self.fee = max(self.estimate_size()*self.fee,
                           constants.min_txn_fee)

    def dictify(self):
        od = OrderedDict()
        od["fee"] = self.fee
        od["fv"] = self.first_valid_round
        if self.genesis_id:
            od["gen"] = self.genesis_id
        od["gh"] = base64.b64decode(self.genesis_hash)
        if self.group:
            od["grp"] = self.group
        od["lv"] = self.last_valid_round
        if self.note:
            od["note"] = self.note
        od["selkey"] = base64.b64decode(self.selkey)
        od["snd"] = encoding.decode_address(self.sender)
        od["type"] = self.type
        od["votefst"] = self.votefst
        od["votekd"] = self.votekd
        od["votekey"] = base64.b64decode(self.votepk)
        od["votelst"] = self.votelst
        return od

    @staticmethod
    def undictify(d):
        note = None
        gen = None
        fv = 0
        grp = None
        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        if "fv" in d:
            fv = d["fv"]
        if "grp" in d:
            grp = d["grp"]
        k = KeyregTxn(encoding.encode_address(d["snd"]), d["fee"], fv,
                      d["lv"], base64.b64encode(d["gh"]).decode(),
                      base64.b64encode(d["votekey"]).decode(),
                      base64.b64encode(d["selkey"]).decode(), d["votefst"],
                      d["votelst"], d["votekd"], note, gen, True)
        k.group = grp
        return k

    def __eq__(self, other):
        if not isinstance(other, KeyregTxn):
            return False
        return (super(KeyregTxn, self).__eq__(self, other) and
                self.votepk == other.votepk and
                self.selkey == other.selkey and
                self.votefst == other.votefst and
                self.votelst == other.votelst and
                self.votekd == other.votekd and
                self.type == other.type)


class AssetConfigTxn(Transaction):
    """
    Represents a transaction for asset creation, reconfiguration, or
    destruction.

    To create an asset, include the following:
        total, default_frozen, unit_name, asset_name,
        manager, reserve, freeze, clawback

    To destroy an asset, include the following:
        creator, index

    To update asset configuration, include the following:
        creator, index, manager, reserve, freeze, clawback

    Args:
        sender (str): address of the sender
        fee (int): transaction fee (per byte if flat_fee is false)
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesis_hash
        creator (str, optional): creator of the asset
        index (int, optional): index of the asset
        total (int, optional): total number of units of this asset created
        default_frozen (bool, optional): whether slots for this asset in user
            accounts are frozen by default
        unit_name (bytes, optional): hint for the name of a unit of this asset
            (8 bytes)
        asset_name (bytes, optional): hint for the name of the asset (32 bytes)
        manager (str, optional): address allowed to change nonzero addresses
            for this asset
        reserve (str, optional): account whose holdings of this asset should
            be reported as "not minted"
        freeze (str, optional): account allowed to change frozen state of
            holdings of this asset
        clawback (str, optional): account allowed take units of this asset
            from any account
        note (bytes, optional): arbitrary optional bytes
        gen (str, optional): genesis_id
        flat_fee (bool): whether the specified fee is a flat fee

    Attributes:
        sender (str)
        fee (int)
        first_valid_round (int)
        last_valid_round (int)
        genesis_hash (str)
        creator (str)
        index (int)
        total (int)
        default_frozen (bool)
        unit_name (bytes)
        asset_name (bytes)
        manager (str)
        reserve (str)
        freeze (str)
        clawback (str)
        note (bytes)
        genesis_id (str)
        type (str)
    """

    def __init__(self, sender, fee, first, last, gh, creator=None, index=None,
                 total=None, default_frozen=None, unit_name=None,
                 asset_name=None, manager=None, reserve=None, freeze=None,
                 clawback=None, note=None, gen=None, flat_fee=False):
        Transaction.__init__(self,  sender, fee, first, last, note, gen, gh)
        self.creator = creator
        self.index = index
        self.total = total
        self.default_frozen = default_frozen
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.manager = manager
        self.reserve = reserve
        self.freeze = freeze
        self.clawback = clawback
        self.type = constants.assetconfig_txn
        if flat_fee:
            self.fee = max(constants.min_txn_fee, self.fee)
        else:
            self.fee = max(self.estimate_size()*self.fee,
                           constants.min_txn_fee)

    def dictify(self):
        od = OrderedDict()

        if (self.total or self.default_frozen or self.unit_name or
                self.asset_name or self.manager or self.reserve or
                self.freeze or self.clawback):
            apar = OrderedDict()
            if self.asset_name:
                apar["an"] = self.asset_name
            if self.clawback:
                apar["c"] = encoding.decode_address(self.clawback)
            if self.default_frozen:
                apar["df"] = self.default_frozen
            if self.freeze:
                apar["f"] = encoding.decode_address(self.freeze)
            if self.manager:
                apar["m"] = encoding.decode_address(self.manager)
            if self.reserve:
                apar["r"] = encoding.decode_address(self.reserve)
            if self.total:
                apar["t"] = self.total
            if self.unit_name:
                apar["un"] = self.unit_name
            od["apar"] = apar

        if self.creator or self.index:
            caid = OrderedDict()
            if self.creator:
                caid["c"] = encoding.decode_address(self.creator)
            if self.index:
                caid["i"] = self.index
            od["caid"] = caid

        od["fee"] = self.fee
        od["fv"] = self.first_valid_round
        if self.genesis_id:
            od["gen"] = self.genesis_id
        od["gh"] = base64.b64decode(self.genesis_hash)
        od["lv"] = self.last_valid_round
        if self.note:
            od["note"] = self.note
        od["snd"] = encoding.decode_address(self.sender)
        od["type"] = self.type

        return od

    @staticmethod
    def undictify(d):
        note = None
        gen = None
        fv = 0

        creator = None
        index = None
        total = None
        default_frozen = None
        unit_name = None
        asset_name = None
        manager = None
        reserve = None
        freeze = None
        clawback = None

        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        if "fv" in d:
            fv = d["fv"]
        if "caid" in d:
            if "c" in d["caid"]:
                creator = encoding.encode_address(d["caid"]["c"])
            if "i" in d["caid"]:
                index = d["caid"]["i"]
        if "apar" in d:
            if "t" in d["apar"]:
                total = d["apar"]["t"]
            if "df" in d["apar"]:
                default_frozen = d["apar"]["df"]
            if "un" in d["apar"]:
                unit_name = d["apar"]["un"]
            if "an" in d["apar"]:
                asset_name = d["apar"]["an"]
            if "m" in d["apar"]:
                manager = encoding.encode_address(d["apar"]["m"])
            if "r" in d["apar"]:
                reserve = encoding.encode_address(d["apar"]["r"])
            if "f" in d["apar"]:
                freeze = encoding.encode_address(d["apar"]["f"])
            if "c" in d["apar"]:
                clawback = encoding.encode_address(d["apar"]["c"])

        ac = AssetConfigTxn(encoding.encode_address(d["snd"]), d["fee"], fv,
                            d["lv"], base64.b64encode(d["gh"]).decode(),
                            creator, index, total, default_frozen,
                            unit_name, asset_name, manager, reserve, freeze,
                            clawback, note, gen, True)
        return ac

    def __eq__(self, other):
        if not isinstance(other, AssetConfigTxn):
            return False
        return (super(AssetConfigTxn, self).__eq__(other) and
                self.creator == other.creator and
                self.index == other.index and
                self.total == other.total and
                self.default_frozen == other.default_frozen and
                self.unit_name == other.unit_name and
                self.asset_name == other.asset_name and
                self.manager == other.manager and
                self.reserve == other.reserve and
                self.freeze == other.freeze and
                self.clawback == other.clawback and
                self.type == other.type)

class AssetFreezeTxn(Transaction):
    """
    Represents a transaction for freezing or unfreezing an account's asset holdings.
    Must be issued by the asset's freeze manager.

    Args:
        sender (str): address of the sender, who must be the asset's freeze manager.
        fee (int): transaction fee (per byte if flat_fee is false)
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesis_hash
        creator (str): creator of the asset
        index (int): index of the asset
        target (str): address having its assets frozen or unfrozen
        new_freeze_state (bool): true if the assets should be frozen, false if they should be transferrable
        note (bytes, optional): arbitrary optional bytes
        gen (str, optional): genesis_id
        flat_fee (bool): whether the specified fee is a flat fee

    Attributes:
        sender (str)
        fee (int)
        first_valid_round (int)
        last_valid_round (int)
        genesis_hash (str)
        creator (str)
        index (int)
        target (str)
        new_freeze_state (bool)
        note (bytes)
        genesis_id (str)
        type (str)
    """

    def __init__(self, sender, fee, first, last, gh, creator, index, target, new_freeze_state,
                 note=None, gen=None, flat_fee=False):
        Transaction.__init__(self, sender, fee, first, last, note, gen, gh)
        self.creator = creator
        self.index = index
        self.target = target
        self.new_freeze_state = new_freeze_state
        self.type = constants.assetfreeze_txn
        if flat_fee:
            self.fee = max(constants.min_txn_fee, self.fee)
        else:
            self.fee = max(self.estimate_size()*self.fee,
                           constants.min_txn_fee)

    def dictify(self):
        od = OrderedDict()

        od["fadd"] = encoding.decode_address(self.target)

        faid = OrderedDict()
        if self.creator:
            faid["c"] = encoding.decode_address(self.creator)
        if self.index:
            faid["i"] = self.index
        od["faid"] = faid

        od["afrz"] = self.new_freeze_state

        od["fee"] = self.fee
        od["fv"] = self.first_valid_round
        if self.genesis_id:
            od["gen"] = self.genesis_id
        od["gh"] = base64.b64decode(self.genesis_hash)
        od["lv"] = self.last_valid_round
        if self.note:
            od["note"] = self.note
        od["snd"] = encoding.decode_address(self.sender)
        od["type"] = self.type

        return od

    @staticmethod
    def undictify(d):
        note = None
        gen = None
        fv = 0
        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        if "fv" in d:
            fv = d["fv"]
        creator = encoding.encode_address(d["faid"]["c"])
        index = d["faid"]["i"]
        target = encoding.encode_address(d["fadd"])
        new_freeze_state = d["afrz"]

        af = AssetFreezeTxn(encoding.encode_address(d["snd"]), d["fee"], fv, d["lv"],
                            base64.b64encode(d["gh"]).decode(), creator, index, target,
                            new_freeze_state, note, gen, True)
        return af

    def __eq__(self, other):
        if not isinstance(other, AssetFreezeTxn):
            return False
        return (super(AssetFreezeTxn, self).__eq__(other) and
                self.creator == other.creator and
                self.index == other.index and
                self.target == other.target and
                self.new_freeze_state == other.new_freeze_state and
                self.type == other.type)

class AssetTransferTxn(Transaction):
    """
    Represents a transaction for asset transfer.

    To begin accepting an asset, supply the same address as both sender and receiver, and set amount to 0.

    To revoke an asset, set revocation_target, and issue the transaction from the asset's revocation manager account.

    To burn or mint an asset, send the asset to or from the asset's reserve account, respectively.

    Args:
        sender (str): address of the sender
        fee (int): transaction fee (per byte if flat_fee is false)
        first (int): first round for which the transaction is valid
        last (int): last round for which the transaction is valid
        gh (str): genesis_hash
        receiver (str): address of the receiver
        amt (int): amount of asset units to send
        creator (str: creator of the asset
        index (int): index of the asset
        close_assets_to (string, optional): send all of sender's remaining assets,
            after paying `amt` to receiver, to this address
        revocation_target (string, optional): send assets from this address, rather than the sender's address
            (can only be used by an asset's revocation manager, also known as clawback)
        note (bytes, optional): arbitrary optional bytes
        gen (str, optional): genesis_id
        flat_fee (bool): whether the specified fee is a flat fee

    Attributes:
        sender (str)
        fee (int)
        first_valid_round (int)
        last_valid_round (int)
        genesis_hash (str)
        creator (str)
        index (int)
        amount (int)
        receiver (string)
        close_assets_to (string)
        revocation_target (string)
        note (bytes)
        genesis_id (str)
        type (str)
    """

    def __init__(self, sender, fee, first, last, gh, receiver, amt, creator, index,
                 close_assets_to=None, revocation_target=None, note=None, gen=None, flat_fee=False):
        Transaction.__init__(self,  sender, fee, first, last, note, gen, gh)
        self.type = constants.assettransfer_txn
        self.receiver = receiver
        self.amount = amt
        self.creator = creator
        self.index = index
        if close_assets_to is not None:
            self.close_assets_to = close_assets_to
        if revocation_target is not None:
            self.revocation_target = revocation_target
        if flat_fee:
            self.fee = max(constants.min_txn_fee, self.fee)
        else:
            self.fee = max(self.estimate_size()*self.fee,
                           constants.min_txn_fee)

    def dictify(self):
        od = OrderedDict()

        xaid = OrderedDict()
        if self.creator:
            xaid["c"] = encoding.decode_address(self.creator)
        if self.index:
            xaid["i"] = self.index
        od["xaid"] = xaid

        if self.revocation_target is not None:
            od["asnd"] = encoding.decode_address(self.revocation_target)
        if self.close_assets_to is not None:
            od["aclose"] = encoding.decode_address(self.close_assets_to)

        od["aamt"] = self.amount
        od["arcv"] = encoding.decode_address(self.receiver)

        od["fee"] = self.fee
        od["fv"] = self.first_valid_round
        if self.genesis_id:
            od["gen"] = self.genesis_id
        od["gh"] = base64.b64decode(self.genesis_hash)
        od["lv"] = self.last_valid_round
        if self.note:
            od["note"] = self.note
        od["snd"] = encoding.decode_address(self.sender)
        od["type"] = self.type

        return od

    @staticmethod
    def undictify(d):

        note = None
        gen = None
        fv = 0
        receiver = None
        amt = 0
        creator = None
        index = None
        close_assets_to = None
        revocation_target = None
        if "note" in d:
            note = d["note"]
        if "gen" in d:
            gen = d["gen"]
        if "fv" in d:
            fv = d["fv"]
        if "arcv" in d:
            receiver = encoding.encode_address(d["arcv"])
        if "aamt" in d:
            amt = d["aamt"]
        if "xaid" in d:
            if "c" in d["xaid"]:
                creator = encoding.encode_address(d["xaid"]["c"])
            if "i" in d["xaid"]:
                index = d["xaid"]["i"]
        if "aclose" in d:
            close_assets_to = encoding.encode_address(d["aclose"])
        if "asnd" in d:
            revocation_target = encoding.encode_address(d["asnd"])

        atxfer = AssetTransferTxn(encoding.encode_address(d["snd"]), d["fee"], fv,
                                  d["lv"], base64.b64encode(d["gh"]).decode(),
                                  receiver, amt, creator, index, close_assets_to, revocation_target,
                                  note, gen, True)
        return atxfer

    def __eq__(self, other):
        if not isinstance(other, AssetTransferTxn):
            return False
        return (super(AssetTransferTxn, self).__eq__(other) and
                self.creator == other.creator and
                self.index == other.index and
                self.amount == other.amount and
                self.receiver == other.receiver and
                self.close_assets_to == other.close_assets_to and
                self.revocation_target == other.revocation_target and
                self.type == other.type)


class SignedTransaction:
    """
    Represents a signed transaction.

    Args:
        transaction (Transaction): transaction that was signed
        signature (str): signature of a single address

    Attributes:
        transaction (Transaction)
        signature (str)
    """
    def __init__(self, transaction, signature):
        self.signature = signature
        self.transaction = transaction

    def dictify(self):
        od = OrderedDict()
        if self.signature:
            od["sig"] = base64.b64decode(self.signature)
        od["txn"] = self.transaction.dictify()
        return od

    @staticmethod
    def undictify(d):
        sig = None
        if "sig" in d:
            sig = base64.b64encode(d["sig"]).decode()
        txn_type = d["txn"]["type"]
        if txn_type == constants.payment_txn:
            txn = PaymentTxn.undictify(d["txn"])
        elif txn_type == constants.keyreg_txn:
            txn = KeyregTxn.undictify(d["txn"])
        elif txn_type == constants.assetconfig_txn:
            txn = AssetConfigTxn.undictify(d["txn"])
        elif txn_type == constants.assettransfer_txn:
            txn = AssetTransferTxn.undictify(d["txn"])
        stx = SignedTransaction(txn, sig)
        return stx

    def __eq__(self, other):
        if not isinstance(other, SignedTransaction):
            return False
        return (self.transaction == other.transaction and
                self.signature == other.signature)


class MultisigTransaction:
    """
    Represents a signed transaction.

    Args:
        transaction (Transaction): transaction that was signed
        multisig (Multisig): multisig account and signatures

    Attributes:
        transaction (Transaction)
        multisig (Multisig)
    """
    def __init__(self, transaction, multisig):
        self.transaction = transaction
        self.multisig = multisig

    def sign(self, private_key):
        """
        Sign the multisig transaction.

        Args:
            private_key (str): private key of signing account

        Note:
            A new signature will replace the old if there is already a
            signature for the address. To sign another transaction, you can
            either overwrite the signatures in the current Multisig, or you
            can use Multisig.get_multisig_account() to get a new multisig
            object with the same addresses.
        """
        self.multisig.validate()
        addr = self.multisig.address()
        if not self.transaction.sender == addr:
            raise error.BadTxnSenderError
        index = -1
        public_key = base64.b64decode(bytes(private_key, "utf-8"))
        public_key = public_key[constants.signing_key_len_bytes:]
        for s in range(len(self.multisig.subsigs)):
            if self.multisig.subsigs[s].public_key == public_key:
                index = s
                break
        if index == -1:
            raise error.InvalidSecretKeyError
        sig = self.transaction.raw_sign(private_key)
        self.multisig.subsigs[index].signature = sig

    def dictify(self):
        od = OrderedDict()
        if self.multisig:
            od["msig"] = self.multisig.dictify()
        od["txn"] = self.transaction.dictify()
        return od

    @staticmethod
    def undictify(d):
        msig = None
        if "msig" in d:
            msig = Multisig.undictify(d["msig"])
        txn_type = d["txn"]["type"]
        if txn_type == constants.payment_txn:
            txn = PaymentTxn.undictify(d["txn"])
        elif txn_type == constants.keyreg_txn:
            txn = KeyregTxn.undictify(d["txn"])
        elif txn_type == constants.assetconfig_txn:
            txn = AssetConfigTxn.undictify(d["txn"])
        mtx = MultisigTransaction(txn, msig)
        return mtx

    @staticmethod
    def merge(part_stxs):
        """
        Merge partially signed multisig transactions.

        Args:
            part_stxs (MultisigTransaction[]): list of partially signed
                multisig transactions

        Returns:
            MultisigTransaction: multisig transaction containing signatures

        Note:
            Only use this if you are given two partially signed multisig
            transactions. To append a signature to a multisig transaction, just
            use MultisigTransaction.sign()
        """
        ref_addr = None
        for stx in part_stxs:
            if not ref_addr:
                ref_addr = stx.multisig.address()
            elif not stx.multisig.address() == ref_addr:
                raise error.MergeKeysMismatchError
        msigstx = None
        for stx in part_stxs:
            if not msigstx:
                msigstx = stx
            else:
                for s in range(len(stx.multisig.subsigs)):
                    if stx.multisig.subsigs[s].signature:
                        if not msigstx.multisig.subsigs[s].signature:
                            msigstx.multisig.subsigs[s].signature = \
                                stx.multisig.subsigs[s].signature
                        elif not msigstx.multisig.subsigs[s].signature == \
                                stx.multisig.subsigs[s].signature:
                            raise error.DuplicateSigMismatchError
        return msigstx

    def __eq__(self, other):
        if not isinstance(other, MultisigTransaction):
            return False
        return (self.transaction == other.transaction and
                self.multisig == other.multisig)


class Multisig:
    """
    Represents a multisig account and signatures.

    Args:
        version (int): currently, the version is 1
        threshold (int): how many signatures are necessary
        addresses (str[]): addresses in the multisig account

    Attributes:
        version (int)
        threshold (int)
        subsigs (MultisigSubsig[])
    """
    def __init__(self, version, threshold, addresses):
        self.version = version
        self.threshold = threshold
        self.subsigs = []
        for a in addresses:
            self.subsigs.append(MultisigSubsig(encoding.decode_address(a)))

    def validate(self):
        """Check if the multisig account is valid."""
        if not self.version == 1:
            raise error.UnknownMsigVersionError
        if (self.threshold <= 0 or len(self.subsigs) == 0 or
                self.threshold > len(self.subsigs)):
            raise error.InvalidThresholdError

    def address(self):
        """Return the multisig account address."""
        msig_bytes = (bytes(constants.msig_addr_prefix, "utf-8") +
                      bytes([self.version]) + bytes([self.threshold]))
        for s in self.subsigs:
            msig_bytes += s.public_key
        addr = encoding.checksum(msig_bytes)
        return encoding.encode_address(addr)

    def dictify(self):
        od = OrderedDict()
        od["subsig"] = [subsig.dictify() for subsig in self.subsigs]
        od["thr"] = self.threshold
        od["v"] = self.version
        return od

    def json_dictify(self):
        d = {
            "subsig": [subsig.json_dictify() for subsig in self.subsigs],
            "thr": self.threshold,
            "v": self.version
        }
        return d

    @staticmethod
    def undictify(d):
        subsigs = [MultisigSubsig.undictify(s) for s in d["subsig"]]
        msig = Multisig(d["v"], d["thr"], [])
        msig.subsigs = subsigs
        return msig

    def get_multisig_account(self):
        """Return a Multisig object without signatures."""
        msig = Multisig(self.version, self.threshold, self.get_public_keys())
        for s in msig.subsigs:
            s.signature = None
        return msig

    def get_public_keys(self):
        """Return the base32 encoded addresses for the multisig account."""
        pks = [encoding.encode_address(s.public_key) for s in self.subsigs]
        return pks

    def __eq__(self, other):
        if not isinstance(other, Multisig):
            return False
        return (self.version == other.version and
                self.threshold == other.threshold and
                self.subsigs == other.subsigs)


class MultisigSubsig:
    """
    Attributes:
        public_key (bytes)
        signature (bytes)
    """
    def __init__(self, public_key, signature=None):
        self.public_key = public_key
        self.signature = signature

    def dictify(self):
        od = OrderedDict()
        od["pk"] = self.public_key
        if self.signature:
            od["s"] = self.signature
        return od

    def json_dictify(self):
        d = {
            "pk": base64.b64encode(self.public_key).decode()
        }
        if self.signature:
            d["s"] = base64.b64encode(self.signature).decode()
        return d

    @staticmethod
    def undictify(d):
        sig = None
        if "s" in d:
            sig = d["s"]
        mss = MultisigSubsig(d["pk"], sig)
        return mss

    def __eq__(self, other):
        if not isinstance(other, MultisigSubsig):
            return False
        return (self.public_key == other.public_key and
                self.signature == other.signature)


def write_to_file(txns, path, overwrite=True):
    """
    Write signed or unsigned transactions to a file.

    Args:
        txns (Transaction[], SignedTransaction[], or MultisigTransaction[]):\
            can be a mix of the three
        path (str): file to write to
        overwrite (bool): whether or not to overwrite what's already in the
            file; if False, transactions will be appended to the file

    Returns:
        bool: true if the transactions have been written to the file
    """

    f = None
    if overwrite:
        f = open(path, "wb")
    else:
        f = open(path, "ab")

    for txn in txns:
        if isinstance(txn, Transaction):
            enc = msgpack.packb({"txn": txn.dictify()}, use_bin_type=True)
            f.write(enc)
        else:
            enc = msgpack.packb(txn.dictify(), use_bin_type=True)
            f.write(enc)
    f.close()
    return True


def retrieve_from_file(path):
    """
    Retrieve signed or unsigned transactions from a file.

    Args:
        path (str): file to read from

    Returns:
        Transaction[], SignedTransaction[], or MultisigTransaction[]:\
            can be a mix of the three
    """

    f = open(path, "rb")
    txns = []
    unp = msgpack.Unpacker(f, raw=False)
    for txn in unp:
        if "msig" in txn:
            txns.append(MultisigTransaction.undictify(txn))
        elif "sig" in txn:
            txns.append(SignedTransaction.undictify(txn))
        elif txn["txn"]["type"] == constants.payment_txn:
            txns.append(PaymentTxn.undictify(txn["txn"]))
        elif txn["txn"]["type"] == constants.keyreg_txn:
            txns.append(KeyregTxn.undictify(txn["txn"]))
    f.close()
    return txns


class TxGroup:
    def __init__(self, txns):
        assert isinstance(txns, list)
        """
        Transactions specifies a list of transactions that must appear
        together, sequentially, in a block in order for the group to be
        valid.  Each hash in the list is a hash of a transaction with
        the `Group` field omitted.
        """
        self.transactions = txns

    def dictify(self):
        od = OrderedDict()
        od["txlist"] = self.transactions
        return od

    @staticmethod
    def undictify(d):
        txg = TxGroup(d["txlist"])
        return txg


def calculate_group_id(txns):
    """
    Calculate group id for a given list of unsigned transactions

    Args:
        txns (list): list of unsigned transactions

    Returns:
        bytes: checksum value representing the group id
    """
    txids = []
    for txn in txns:
        raw_txn = encoding.msgpack_encode(txn)
        to_hash = constants.txid_prefix + base64.b64decode(raw_txn)
        txids.append(encoding.checksum(to_hash))

    group = TxGroup(txids)

    encoded = encoding.msgpack_encode(group)
    to_sign = constants.tgid_prefix + base64.b64decode(encoded)
    gid = encoding.checksum(to_sign)
    return gid


def assign_group_id(txns, address=None):
    """
    Assign group id to a given list of unsigned transactions

    Args:
        txns (list): list of unsigned transactions
        address (str): optional sender address specifying which transaction return

    Returns:
        txns (list): list of unsigned transactions with group property set
    """
    gid = calculate_group_id(txns)
    result = []
    for tx in txns:
        if address is None or tx.sender == address:
            tx.group = gid
            result.append(tx)
    return result
