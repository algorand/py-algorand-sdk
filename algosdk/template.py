import math
import random
from . import error, encoding, constants, transaction
import base64


class Template:
    def get_address(self):
        """
        Returns the address of this contract.
        """
        p = constants.logic_prefix + base64.b64decode(self.get_program())
        addr = encoding.checksum(p)
        return encoding.encode_address(addr)
    def get_program(self):
        pass


class Split(Template):
    """
    Split allows to lock assets in an account which allows to transfer 
    to two predefined addresses in a specific M:N ratio. Note that the ratio is 
    specified by the first address part. For example - If you would like to have 
    a split where the first address receives 30 percent and the second receives 70, 
    set ratn and ratd to 30 and 100, respectively. 
    Split also have an expiry round, in which the owner can transfer back the assets.
    ...

    Arguments:
        owner (str): an address that can receive the asset after the expiry round
        receiver_1 (str): first address to receive assets 
        receiver_2 (str): second address to receive assets 
        ratn (int): the numerator of the first address fraction
        ratd (int): the denominator of the first address fraction
        expiry_round (int): the round on which the assets can be transferred back to owner 
        min_pay (int): the minimum number of assets that can be transferred from the account
        max_fee (int): half the maximum fee that can be paid to the network by the account

    """
    def __init__(self, owner : str, receiver_1: str, receiver_2: str, ratn : int, ratd : int, expiry_round : int, min_pay : int, max_fee : int):
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
        returns a byte array to be used in a 
        """ 
        orig = "ASAIAQUCAAYHCAkmAyDYHIR7TIW5eM/WAZcXdEDqv7BD+baMN6i2/A5JatGbNCDKsaoZHPQ3Zg8zZB/BZ1oDgt77LGo5np3rbto3/gloTyB40AS2H3I72YCbDk4hKpm7J7NnFy2Xrt39TJG0ORFg+zEQIhIxASMMEDIEJBJAABkxCSgSMQcyAxIQMQglEhAxAiEEDRAiQAAuMwAAMwEAEjEJMgMSEDMABykSEDMBByoSEDMACCEFCzMBCCEGCxIQMwAIIQcPEBA="
        orig = base64.b64decode(orig)
        output = base64.b64encode(inject(orig, [4, 7, 8, 9, 10, 14, 47, 80], [self.max_fee, self.expiry_round, self.ratn, self.ratd, self.min_pay, self.owner, self.receiver_1, self.receiver_2], [int, int, int, int, int, "address", "address", "address"])).decode()
        return output
        
    def get_send_funds_transaction(self, first_valid_round, gh, amount : int, precise = True):
        """
        Return a group transactions array which transfer funds according to the contract's ratio.
        
        Parameters
        ----------
        amount : int
            the amount to be transferred
            
        precise : bool, optional
            precise treats the case where amount is not perfectly divisible based on the ration. 
            When set to False, the amount will be divided as close as possible but one address will get 
            slightly more. When True, an error will be raised. Defaults to True.

        Raises
        ------
        NotDivisibleError
            see precise
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

        txn_1 = transaction.PaymentTxn(self.get_address(), self.max_fee, first_valid_round, self.expiry_round, gh, self.receiver_1, amt_1)
        txn_2 = transaction.PaymentTxn(self.get_address(), self.max_fee, first_valid_round, self.expiry_round, gh, self.receiver_2, amt_2)
        
        transaction.assign_group_id([txn_1, txn_2])

        p = self.get_program()

        lsig = transaction.LogicSig(p)

        stx_1 = transaction.LogicSigTransaction(txn_1, lsig)
        stx_2 = transaction.LogicSigTransaction(txn_2, lsig)

        txn_group = transaction.TxGroup([stx_1, stx_2])
        return txn_group


class HTLC(Template):
    """
    Hash Time Locked Contract allows a user to recieve the Algo prior to a deadline (in terms of a round) by proving a knowledge 
    of a special value or to forfeit the ability to claim, returning it to the payer.
    This contract is usually used to perform cross-chained atomic swaps.
    
    More formally - 
    Algos can be transfered under only two circumstances:
    1. To receiver if hash_function(arg_0) = hash_value
    2. To owner if txn.FirstValid > expiry_round
    ...

    Arguments:
        owner (str): an address that can receive the asset after the expiry round
        receiver (str): address to receive Algos 
        hash_function (str): the hash function to be used (must be either sha256 or keccak256)
        hash_image (str): the hash image in base64
        expiry_round (int): the round on which the assets can be transferred back to owner 
        max_fee (int): the maximum fee that can be paid to the network by the account

    """
    def __init__(self, owner : str, receiver: str, hash_function : str, hash_image : str, expiry_round : int, max_fee : int):
        self.owner = owner
        self.receiver = receiver
        self.hash_function = hash_function
        self.hash_image = hash_image
        self.expiry_round = expiry_round
        self.max_fee = max_fee
        
    def get_program(self):
        """
        returns a byte array to be used in LogicSig
        """ 
        orig = "ASAEBQEABiYDIP68oLsUSlpOp7Q4pGgayA5soQW8tgf8VlMlyVaV9qITAQYg5pqWHm8tX3rIZgeSZVK+mCNe0zNjyoiRi7nJOKkVtvkxASIOMRAjEhAxBzIDEhAxCCQSEDEJKBItASkSEDEJKhIxAiUNEBEQ"
        orig = base64.b64decode(orig)
        hash_inject = 0
        if self.hash_function == "sha256":
            hash_inject = 1
        elif self.hash_function == "keccak256":
            hash_inject = 2
        output = base64.b64encode(inject(orig, [3, 6, 10, 42, 44, 101], [self.max_fee, self.expiry_round, self.receiver, self.hash_image, self.owner, hash_inject], [int, int, "address", "base64", "address", int])).decode()
        return output


class DynamicFee(object):
    """
        DynamicFee contract allows to create a transaction without specifying the fee. The fee will be 
        determined at the moment of transfer. 
        ...

        Attributes
        ----------
        receiver: str
            address to receive the assets 
        amount : int
            amount of assets to transfer 
        first_valid: int
            first valid round for the transaction
        last_valid : int, optional
            last valid round for the transaction (default to first_valid + 1000)
        close_remainder_address : str, optional
            If you would like to close the account after the transfer, specify the address that would recieve the remainder.

        """
        
    def __init__(self, receiver: str, amount: int, first_valid: int, last_valid: int=None, close_remainder_address: str=None):
        self.lease_value = bytes([random.randint(0, 255) for x in range(constants.lease_length)])
        
        if last_valid is None:
            last_valid = first_valid + 1000
            
        self.amount = amount
        self.first_valid = first_valid
        self.close_remainder_address = close_remainder_address
        
    def sign_dynamic_fee(self, secret_key):
        """
        signs the dynamic fee contract
        
        Parameters
        ----------
        secret_key : bytes
            the secret key to sign the contract 

        """ 
        pass
        
    def get_bytes(self):
        """
        returns the bytes representation of the contract to be sent to the delegatee 
        """
        pass
        
    def get_transactions(self, contract, secret_key):
        """
        returns the two transactions needed to complete the transfer 
        
        Parameters
        ----------
        contract : bytes
            the contract containg information, should be recived from payer 
        seceret_key : bytes
            the secret key to sign the contract
        """
        
        # Decode bytes 
        # create the main txn
        # attach the lsig

        # create the auxiliary txn  
        # sign it
        
        # Create and return a group txn
        pass





def put_uvarint(buf, x):
    i = 0
    while x >= 0x80 :
        buf.append((x&0xFF) | 0x80)
        x >>= 7
        i += 1
        
    buf.append(x&0xFF)
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
            dec_len = put_uvarint(buf, val)
            val = bytes(buf)
            res = replace(res, val, offsets[i], 1)

        elif val_type == "address":
            val = encoding.decode_address(val)
            res = replace(res, val, offsets[i], 32)
            
        elif val_type == "base64":
            val = bytes(base64.b64decode(val))
            buf = []
            dec_len = put_uvarint(buf, len(val)) + len(val)
            res = replace(res, bytes(buf) + val, offsets[i], 2)
            
        else:
            raise Exception("Unkown Type")
            
        
        # update offsets 
        if dec_len != 0:
            for o in range(len(offsets)):
                offsets[o] += dec_len - 1
            
    return res
    