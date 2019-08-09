from . import constants
import base64
from nacl.signing import SigningKey


def microalgos_to_algos(microalgos):
    """
    Convert microalgos to algos.

    Args:
        microalgos (int): how many microalgos

    Returns:
        int or float: how many algos
    """
    return microalgos/constants.microalgos_to_algos_ratio


def algos_to_microalgos(algos):
    """
    Convert algos to microalgos.

    Args:
        algos (int or float): how many algos

    Returns:
        int: how many microalgos
    """
    return algos*constants.microalgos_to_algos_ratio


def sign_bytes(to_sign, private_key):
    """
    Sign arbitrary bytes.

    Args:
        to_sign (bytes): bytes to sign

    Returns:
        str: base64 signature
    """
    to_sign = constants.bytes_prefix + to_sign
    private_key = base64.b64decode(bytes(private_key, "utf-8"))
    signing_key = SigningKey(private_key[:constants.signing_key_len_bytes])
    signed = signing_key.sign(to_sign)
    return base64.b64encode(signed.signature).decode()
