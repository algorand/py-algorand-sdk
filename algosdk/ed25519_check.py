"""
Ed25519 curve-point check used for post-quantum address derivation.
"""

from algosdk import constants

_ED25519_P = 2**255 - 19
_ED25519_D = (-121665 * pow(121666, _ED25519_P - 2, _ED25519_P)) % _ED25519_P


def is_ed25519_point(public_key: bytes) -> bool:
    """
    Check whether 32 bytes decode to any point on the ed25519 curve.

    This is the "broad" predicate used for post-quantum address derivation: it
    returns True if the value could be interpreted as a curve point by any
    ed25519 implementation, including small-order points, non-canonical
    encodings, and points outside the prime-order subgroup. It deliberately
    recognizes more encodings as curve points than libsodium's
    crypto_core_ed25519_is_valid_point, so address derivation rejects more
    candidate salts (matching go-algorand's basics.IsEdwards25519Point).

    Args:
        public_key (bytes): 32-byte value to test

    Returns:
        bool: True if the value decodes to an ed25519 point
    """
    if len(public_key) != constants.key_len_bytes:
        return False
    p = _ED25519_P
    # The low 255 bits are y; the top bit encodes the sign of x, which does
    # not affect whether a point exists.
    y = (int.from_bytes(public_key, "little") & ((1 << 255) - 1)) % p
    u = (y * y - 1) % p
    v = (_ED25519_D * y * y + 1) % p
    # A point exists iff x^2 = u / v has a solution, i.e. u / v is a square.
    x = (u * pow(v, 3, p) * pow(u * pow(v, 7, p) % p, (p - 5) // 8, p)) % p
    vxx = (v * x * x) % p
    return vxx == u % p or vxx == (-u) % p
