import math
from . import error, encoding, transaction, logic
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
    have an expiry round, in which the owner can transfer back the
    assets.

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

        lsig = transaction.LogicSig(base64.b64decode(p))

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
