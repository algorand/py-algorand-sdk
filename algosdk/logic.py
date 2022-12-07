import base64
import json
import os
import warnings

from . import constants
from . import error
from . import encoding

from nacl.signing import SigningKey


def address(program):
    """
    Return the address of the program.

    Args:
        program (bytes): compiled program

    Returns:
        str: program address
    """
    to_sign = constants.logic_prefix + program
    checksum = encoding.checksum(to_sign)
    return encoding.encode_address(checksum)


def teal_sign(private_key, data, contract_addr):
    """
    Return the signature suitable for ed25519verify TEAL opcode

    Args:
        private_key (str): private key to sign with
        data (bytes): data to sign
        contract_addr (str): program hash (contract address) to sign for

    Return:
        bytes: signature
    """
    private_key = base64.b64decode(private_key)
    signing_key = SigningKey(private_key[: constants.key_len_bytes])

    to_sign = (
        constants.logic_data_prefix
        + encoding.decode_address(contract_addr)
        + data
    )
    signed = signing_key.sign(to_sign)
    return signed.signature


def teal_sign_from_program(private_key, data, program):
    """
    Return the signature suitable for ed25519verify TEAL opcode

    Args:
        private_key (str): private key to sign with
        data (bytes): data to sign
        program (bytes): program to sign for

    Return:
        bytes: signature
    """

    return teal_sign(private_key, data, address(program))


def get_application_address(appID: int) -> str:
    """
    Return the escrow address of an application.

    Args:
        appID (int): The ID of the application.

    Returns:
        str: The address corresponding to that application's escrow account.
    """
    assert isinstance(
        appID, int
    ), "(Expected an int for appID but got [{}] which has type [{}])".format(
        appID, type(appID)
    )

    to_sign = constants.APPID_PREFIX + appID.to_bytes(8, "big")
    checksum = encoding.checksum(to_sign)
    return encoding.encode_address(checksum)
