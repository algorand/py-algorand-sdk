import math
import random
from . import error, encoding, constants, transaction, logic, account
import base64


class Template:
    def get_address(self):
        """
        Return the address of the contract.
        """
        return logic.address(self.get_program())

    def get_program(self):
        pass


class Split(Template):
    """
    Split allows locking assets in an account which allows transfering
    to two predefined addresses in a specific M:N ratio. Note that the ratio is
    specified by the first address part. For example, if you would like to
    have a split where the first address receives 30 percent and the second
    receives 70, set ratn and ratd to 30 and 100, respectively. Split also
    have an expiry round, in which the owner can transfer back the assets.

    Arguments:
        owner (str): an address that can receive the asset after the expiry
            round
        receiver_1 (str): first address to receive assets
        receiver_2 (str): second address to receive assets
        ratn (int): the numerator of the first address fraction
        ratd (int): the denominator of the first address fraction
        expiry_round (int): the round on which the assets can be transferred
            back to owner
        min_pay (int): the minimum number of assets that can be transferred
            from the account to receiver_1
        max_fee (int): half the maximum fee that can be paid to the network by
            the account
    """
    def __init__(self, owner: str, receiver_1: str, receiver_2: str, ratn: int,
                 ratd: int, expiry_round: int, min_pay: int, max_fee: int):
        self.owner = owner
        self.receiver_1 = receiver_1
        self.receiver_2 = receiver_2
        self.ratn = ratn
        self.ratd = ratd
        self.expiry_round = expiry_round
        self.min_pay = min_pay
        self.max_fee = max_fee

    def get_program(self):
        """
        Return a byte array to be used in LogicSig.
        """
        orig = ("ASAIAQUCAAYHCAkmAyDYHIR7TIW5eM/WAZcXdEDqv7BD+baMN6i2/A5JatG" +
                "bNCDKsaoZHPQ3Zg8zZB/BZ1oDgt77LGo5np3rbto3/gloTyB40AS2H3I72Y" +
                "CbDk4hKpm7J7NnFy2Xrt39TJG0ORFg+zEQIhIxASMMEDIEJBJAABkxCSgSM" +
                "QcyAxIQMQglEhAxAiEEDRAiQAAuMwAAMwEAEjEJMgMSEDMABykSEDMBByoS" +
                "EDMACCEFCzMBCCEGCxIQMwAIIQcPEBA=")
        orig = base64.b64decode(orig)
        offsets = [4, 7, 8, 9, 10, 14, 47, 80]
        values = [self.max_fee, self.expiry_round, self.ratn, self.ratd,
                  self.min_pay, self.owner, self.receiver_1, self.receiver_2]
        types = [int, int, int, int, int, "address", "address", "address"]
        return inject(orig, offsets, values, types)

    def get_send_funds_transaction(self, amount: int, first_valid, last_valid,
                                   gh, precise=True):
        """
        Return a group transactions array which transfers funds according to
        the contract's ratio.

        Args:
            amount (int): amount to be transferred
            first_valid (int): first round where the transactions are valid
            gh (str): genesis hash in base64
            precise (bool, optional): precise treats the case where amount is
                not perfectly divisible based on the ratio. When set to False,
                the amount will be divided as close as possible but one
                address will get slightly more. When True, an error will be
                raised. Defaults to True.

        Returns:
            Transaction[]

        Raises:
            NotDivisibleError: see precise
        """
        amt_1 = 0
        amt_2 = 0

        gcd = math.gcd(self.ratn, self.ratd)
        ratn = self.ratn // gcd
        ratd = self.ratd // gcd

        if amount % ratd == 0:
            amt_1 = amount // ratd * ratn
            amt_2 = amount - amt_2
        elif precise:
            raise error.NotDivisibleError
        else:
            amt_1 = round(amount / ratd * ratn)
            amt_2 = amount - amt_1

        txn_1 = transaction.PaymentTxn(self.get_address(), self.max_fee,
                                       first_valid, last_valid, gh,
                                       self.receiver_1, amt_1)
        txn_2 = transaction.PaymentTxn(self.get_address(), self.max_fee,
                                       first_valid, last_valid, gh,
                                       self.receiver_2, amt_2)

        transaction.assign_group_id([txn_1, txn_2])

        p = self.get_program()

        lsig = transaction.LogicSig(p)

        stx_1 = transaction.LogicSigTransaction(txn_1, lsig)
        stx_2 = transaction.LogicSigTransaction(txn_2, lsig)

        return [stx_1, stx_2]


class HTLC(Template):
    """
    Hash Time Locked Contract allows a user to recieve the Algo prior to a
    deadline (in terms of a round) by proving knowledge of a special value
    or to forfeit the ability to claim, returning it to the payer.
    This contract is usually used to perform cross-chained atomic swaps.

    More formally, algos can be transfered under only two circumstances:
        1. To receiver if hash_function(arg_0) = hash_value
        2. To owner if txn.FirstValid > expiry_round

    Args:
        owner (str): an address that can receive the asset after the expiry
            round
        receiver (str): address to receive Algos
        hash_function (str): the hash function to be used (must be either
            sha256 or keccak256)
        hash_image (str): the hash image in base64
        expiry_round (int): the round on which the assets can be transferred
            back to owner
        max_fee (int): the maximum fee that can be paid to the network by the
            account

    """
    def __init__(self, owner: str, receiver: str, hash_function: str,
                 hash_image: str, expiry_round: int, max_fee: int):
        self.owner = owner
        self.receiver = receiver
        self.hash_function = hash_function
        self.hash_image = hash_image
        self.expiry_round = expiry_round
        self.max_fee = max_fee

    def get_program(self):
        """
        Return a byte array to be used in LogicSig.
        """
        orig = ("ASAEBQEABiYDIP68oLsUSlpOp7Q4pGgayA5soQW8tgf8VlMlyVaV9qITAQ" +
                "Yg5pqWHm8tX3rIZgeSZVK+mCNe0zNjyoiRi7nJOKkVtvkxASIOMRAjEhAx" +
                "BzIDEhAxCCQSEDEJKBItASkSEDEJKhIxAiUNEBEQ")
        orig = base64.b64decode(orig)
        hash_inject = 0
        if self.hash_function == "sha256":
            hash_inject = 1
        elif self.hash_function == "keccak256":
            hash_inject = 2
        offsets = [3, 6, 10, 42, 45, 102]
        values = [self.max_fee, self.expiry_round, self.receiver,
                  self.hash_image, self.owner, hash_inject]
        types = [int, int, "address", "base64", "address", int]
        return inject(orig, offsets, values, types)


class DynamicFee(Template):
    """
    DynamicFee contract allows you to create a transaction without
    specifying the fee. The fee will be determined at the moment of
    transfer.

    Args:
        receiver (str): address to receive the assets
        amount (int): amount of assets to transfer
        first_valid (int): first valid round for the transaction
        last_valid (int, optional): last valid round for the transaction
            (defaults to first_valid + 1000)
        close_remainder_address (str): the address that recieves the remainder
    """

    def __init__(self, receiver: str, amount: int, first_valid: int,
                 last_valid: int = None, close_remainder_address: str = None):
        self.lease_value = bytes([random.randint(0, 255) for x in range(
                                 constants.lease_length)])

        self.last_valid = last_valid
        if last_valid is None:
            last_valid = first_valid + 1000

        self.amount = amount
        self.first_valid = first_valid
        self.close_remainder_address = close_remainder_address
        self.receiver = receiver

    def get_program(self):
        """
        Return a byte array to be used in LogicSig.
        """
        orig = ("ASAFAgEFBgcmAyD+vKC7FEpaTqe0OKRoGsgObKEFvLYH/FZTJclWlfaiEy" +
                "DmmpYeby1feshmB5JlUr6YI17TM2PKiJGLuck4qRW2+QEGMgQiEjMAECMS" +
                "EDMABzEAEhAzAAgxARIQMRYjEhAxECMSEDEHKBIQMQkpEhAxCCQSEDECJR" +
                "IQMQQhBBIQMQYqEhA=")
        orig = base64.b64decode(orig)
        offsets = [5, 6, 7, 11, 44, 76]
        values = [self.amount, self.first_valid, self.last_valid,
                  self.receiver, self.close_remainder_address,
                  base64.b64encode(self.lease_value)]
        types = [int, int, int, "address", "address", "base64"]
        return inject(orig, offsets, values, types)

    @staticmethod
    def get_transactions(txn, lsig, private_key, fee):
        """
        Create and sign the secondary dynamic fee transaction, update
        transaction fields, and sign as the fee payer; return both
        transactions.

        Args:
            txn (Transaction): main transaction from payer
            lsig (LogicSig): signed logic received from payer
            private_key (str): the secret key of the account that pays the fee
                in base64
            fee (int): fee per byte, for both transactions
        """
        txn.fee = fee
        txn.fee = max(constants.min_txn_fee, fee*txn.estimate_size())

        # reimbursement transaction
        address = account.address_from_private_key(private_key)
        txn_2 = transaction.PaymentTxn(address, fee, txn.first_valid_round,
                                       txn.last_valid_round, txn.genesis_hash,
                                       txn.sender, txn.fee, lease=txn.lease)

        transaction.assign_group_id([txn_2, txn])

        stx_1 = transaction.LogicSigTransaction(txn, lsig)
        stx_2 = txn_2.sign(private_key)

        return [stx_2, stx_1]

    def sign_dynamic_fee(self, private_key, gh):
        """
        Return the main transaction and signed logic needed to complete the
        transfer. These should be sent to the fee payer, who can use
        get_transactions() to update fields and create the auxiliary
        transaction.

        Args:
            private_key (bytes): the secret key to sign the contract in base64
            gh (str): genesis hash, in base64
        """
        sender = account.address_from_private_key(private_key)

        # main transaction
        close = None if self.close_remainder_address == bytes(
            constants.address_len) else self.close_remainder_address
        txn = transaction.PaymentTxn(sender, 0, self.first_valid,
                                     self.last_valid, gh, self.receiver,
                                     self.amount, lease=self.lease_value,
                                     close_remainder_to=close)
        lsig = transaction.LogicSig(self.get_program())
        lsig.sign(private_key)

        return txn, lsig


class PeriodicPayment(Template):
    """
    PeriodicPayment contract enables creating an account which allows the
    withdrawal of a fixed amount of assets every fixed number of rounds to a
    specific Algrorand Address. In addition, the contract allows to add
    timeout, after which the address can withdraw the rest of the assets.

    Args:
        receiver (str): address to receive the assets
        amount (int): amount of assets to transfer at every cycle
        withdrawing_window (int): the number of blocks in which the user can
            withdraw the asset once the period start (must be < 1000)
        period (int): how often the address can withdraw assets (in rounds)
        fee (int): maximum fee per transaction
        timeout (int): a round in which the receiver can withdraw the rest of
            the funds after
    """
    def __init__(self, receiver: str, amount: int, withdrawing_window: int,
                 period: int, max_fee: int, timeout: int):
        self.lease_value = bytes([random.randint(0, 255) for x in range(
                                 constants.lease_length)])
        self.receiver = receiver
        self.amount = amount
        self.withdrawing_window = withdrawing_window
        self.period = period
        self.max_fee = max_fee
        self.timeout = timeout

    def get_program(self):
        """
        Return a byte array to be used in LogicSig.
        """
        orig = ("ASAHAQoLAAwNDiYCAQYg/ryguxRKWk6ntDikaBrIDmyhBby2B/xWUyXJVp" +
                "X2ohMxECISMQEjDhAxAiQYJRIQMQQhBDECCBIQMQYoEhAxCTIDEjEHKRIQ" +
                "MQghBRIQMQkpEjEHMgMSEDECIQYNEDEIJRIQERA=")
        orig = base64.b64decode(orig)
        offsets = [4, 5, 7, 8, 9, 12, 15]
        values = [self.max_fee, self.period, self.withdrawing_window,
                  self.amount, self.timeout, base64.b64encode(
                      self.lease_value), self.receiver]
        types = [int, int, int, int, int, "base64", "address"]
        return inject(orig, offsets, values, types)

    @staticmethod
    def get_withdrawal_transaction(contract, first_valid, gh, fee):
        """
        Return the withdrawal transaction to be sent to the network.

        Args:
            contract (bytes): contract containing information, should be
                received from payer
            first_valid (int): first round the transaction should be valid;
                this must be a multiple of self.period
            gh (str): genesis hash in base64
            fee (int): fee per byte
        """
        address = logic.address(contract)
        _, ints, bytearrays = logic.read_program(contract)
        if not (len(ints) == 7 and len(bytearrays) == 2):
            raise error.WrongContractError("Wrong contract provided; " +
                                           "a periodic payment contra" +
                                           "ct is needed")
        amount = ints[5]
        withdrawing_window = ints[4]
        period = ints[2]
        lease_value = bytearrays[0]
        receiver = encoding.encode_address(bytearrays[1])

        if first_valid % period != 0:
            raise error.PeriodicPaymentDivisibilityError
        txn = transaction.PaymentTxn(address, fee,
                                     first_valid, first_valid +
                                     withdrawing_window, gh,
                                     receiver, amount,
                                     lease=lease_value)

        lsig = transaction.LogicSig(contract)
        stx = transaction.LogicSigTransaction(txn, lsig)
        return stx


class LimitOrder(Template):
    """
    Limit Order allows to trade Algos for other asests given a specific ratio;
    for N Algos, swap for Rate * N Assets.
    ...

    Args:
        owner (str): an address that can receive the asset after the expiry
            round
        asset_id (int): asset to be transfered
        ratn (int): the numerator of the exchange rate
        ratd (int): the denominator of the exchange rate
        expiry_round (int): the round on which the assets can be transferred
            back to owner
        min_trade (int): the minimum amount (of Algos) to be traded away
        max_fee (int): the maximum fee that can be paid to the network by the
            account

    """
    def __init__(self, owner: str, asset_id: int, ratn: int, ratd: int,
                 expiry_round: int, max_fee: int, min_trade: int):
        self.owner = owner
        self.ratn = ratn
        self.ratd = ratd
        self.expiry_round = expiry_round
        self.min_trade = min_trade
        self.max_fee = max_fee
        self.asset_id = asset_id

    def get_program(self):
        """
        Return a byte array to be used in LogicSig.
        """
        orig = ("ASAKAAEFAgYEBwgJHSYBIJKvkYTkEzwJf2arzJOxERsSogG9nQzKPkpIoc" +
                "4TzPTFMRYiEjEQIxIQMQEkDhAyBCMSQABVMgQlEjEIIQQNEDEJMgMSEDMB" +
                "ECEFEhAzAREhBhIQMwEUKBIQMwETMgMSEDMBEiEHHTUCNQExCCEIHTUENQ" +
                "M0ATQDDUAAJDQBNAMSNAI0BA8QQAAWADEJKBIxAiEJDRAxBzIDEhAxCCIS" +
                "EBA=")
        orig = base64.b64decode(orig)
        offsets = [5, 7, 9, 10, 11, 12, 16]
        values = [self.max_fee, self.min_trade, self.asset_id, self.ratd,
                  self.ratn, self.expiry_round, self.owner]
        types = [int, int, int, int, int, int, "address"]
        return inject(orig, offsets, values, types)

    def get_swap_assets_transactions(self, amount: int, contract: bytes,
                                     private_key: str, first_valid,
                                     last_valid, gh, fee):
        """
        Return a group transactions array which transfer funds according to
        the contract's ratio.

        Args:
            amount (int): the amount of assets to be sent
            contract (bytes): the contract containg information, should be
                recieved from payer
            private_key (str): the secret key to sign the contract
            first_valid (int): first valid round for the transactions
            last_valid (int): last valid round for the transactions
            gh (str): genesis hash in base64
            fee (int): fee per byte
        """
        txn_1 = transaction.PaymentTxn(self.get_address(), fee,
                                       first_valid, last_valid, gh,
                                       account.address_from_private_key(
                                       private_key), int(
                                           amount/self.ratn*self.ratd))

        txn_2 = transaction.AssetTransferTxn(account.address_from_private_key(
                                             private_key), fee,
                                             first_valid, last_valid, gh,
                                             self.owner, amount,
                                             self.asset_id)

        transaction.assign_group_id([txn_1, txn_2])

        lsig = transaction.LogicSig(contract)
        stx_1 = transaction.LogicSigTransaction(txn_1, lsig)
        stx_2 = txn_2.sign(private_key)

        return [stx_1, stx_2]


def put_uvarint(buf, x):
    i = 0
    while x >= 0x80:
        buf.append((x & 0xFF) | 0x80)
        x >>= 7
        i += 1

    buf.append(x & 0xFF)
    return i + 1


def inject(orig, offsets, values, values_types):
    # make sure we have enough values
    assert len(offsets) == len(values) == len(values_types)

    res = orig[:]

    def replace(arr, new_val, offset, place_holder_length):
        return arr[:offset] + new_val + arr[offset+place_holder_length:]

    for i in range(len(offsets)):
        val = values[i]
        val_type = values_types[i]
        dec_len = 0

        if val_type == int:
            buf = []
            dec_len = put_uvarint(buf, val) - 1
            val = bytes(buf)
            res = replace(res, val, offsets[i], 1)

        elif val_type == "address":
            val = encoding.decode_address(val)
            res = replace(res, val, offsets[i], 32)

        elif val_type == "base64":
            val = bytes(base64.b64decode(val))
            buf = []
            dec_len = put_uvarint(buf, len(val)) + len(val) - 2
            res = replace(res, bytes(buf) + val, offsets[i], 2)

        else:
            raise Exception("Unkown Type")

        # update offsets
        if dec_len != 0:
            for o in range(len(offsets)):
                offsets[o] += dec_len

    return res
