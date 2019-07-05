from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from nacl import signing
import base64
from . import wordlist
from . import error


# get the wordlist
word_list = wordlist.word_list_raw().split("\n")


def from_master_derivation_key(key):
    """
    Return the mnemonic for the master derivation key (base64).

    Args:
        key (str): master derivation key

    Returns:
        str: mnemonic

    """
    key = base64.b64decode(key)
    return from_key(key)


def to_master_derivation_key(mnemonic):
    """
    Return the master derivation key for the mnemonic.

    Args:
        mnemonic (str): mnemonic of the master derivation key

    Returns:
        str: master derivation key
    """
    key_bytes = to_key(mnemonic)
    return base64.b64encode(key_bytes).decode()


def from_private_key(key):
    """
    Return the mnemonic for the private key.

    Args:
        key (str): private key in base64

    Returns:
        str: mnemonic
    """
    key = base64.b64decode(key)
    return from_key(key[:32])


def to_private_key(mnemonic):
    """
    Return the private key for the mnemonic.

    Args:
        mnemonic (str): mnemonic of the private key

    Returns:
        str: private key in base64
    """
    key_bytes = to_key(mnemonic)
    key = signing.SigningKey(key_bytes)
    return base64.b64encode(key.encode() + key.verify_key.encode()).decode()


def from_key(key):
    """
    Return the mnemonic for the key.

    Args:
        key (bytes): key to compute mnemonic of

    Returns:
        str: mnemonic
    """
    if not len(key) == 32:
        raise error.WrongKeyBytesLengthError
    chksum = checksum(key)
    nums = to_11_bit(key)
    words = apply_words(nums)
    return " ".join(words) + " " + chksum


def to_key(mnemonic):
    """
    Give the corresponding key for the mnemonic.

    Args:
        mnemonic (str): mnemonic for the key

    Returns:
        bytes: key
    """
    mnemonic = mnemonic.split(" ")
    if not len(mnemonic) == 25:
        raise error.WrongMnemonicLengthError
    m_checksum = mnemonic[-1]
    mnemonic = from_words(mnemonic[:-1])
    m_bytes = to_bytes(mnemonic)
    if not m_bytes[-1:len(m_bytes)] == bytes([0]):
        raise error.WrongChecksumError
    chksum = checksum(m_bytes[:32])
    if chksum.__eq__(m_checksum):
        return m_bytes[:32]
    else:
        raise error.WrongChecksumError


def checksum(data):
    """
    Compute the mnemonic checksum.

    Args:
        data (bytes): data to compute checksum of

    Returns:
        bytes: checksum
    """
    hash = hashes.Hash(hashes.SHA512_256(), default_backend())
    hash.update(data)
    chksum = hash.finalize()
    temp = chksum[0:2]
    nums = to_11_bit(temp)
    return apply_words(nums)[0]


def apply_words(nums):
    """
    Get the corresponding words for a list of 11-bit numbers.

    Args:
        nums (int[]): list of 11-bit numbers

    Returns:
        str[]: list of words
    """
    words = []
    for n in nums:
        words.append(word_list[n])
    return words


def from_words(words):
    """
    Get the corresponding 11-bit numbers for a list of words.

    Args:
        words (str[]): list of words

    Returns:
        int[]: list of 11-bit numbers
    """
    nums = []
    for w in words:
        nums.append(word_list.index(w))
    return nums


def to_11_bit(data):
    """
    Convert a bytearray to an list of 11-bit numbers.

    Args:
        data (bytes): bytearray to convert to 11-bit numbers

    Returns:
        int[]: list of 11-bit numbers
    """
    buffer = 0
    num_of_bits = 0
    output = []
    for i in range(len(data)):
        buffer |= data[i] << num_of_bits
        num_of_bits += 8
        if num_of_bits >= 11:
            output.append(buffer & 2047)
            buffer = buffer >> 11
            num_of_bits -= 11
    if num_of_bits != 0:
        output.append(buffer & 2047)
    return output


def to_bytes(nums):
    """
    Convert a list of 11-bit numbers to a bytearray.

    Args:
        nums (int[]): list of 11-bit numbers

    Returns:
        bytes: bytearray
    """
    buffer = 0
    num_of_bits = 0
    output = []
    for i in range(len(nums)):
        buffer |= nums[i] << num_of_bits
        num_of_bits += 11
        while num_of_bits >= 8:
            output.append(buffer & 255)
            buffer = buffer >> 8
            num_of_bits -= 8
    if num_of_bits != 0:
        output.append(buffer & 255)
    return bytes(output)
