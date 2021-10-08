from .base_type import Type
from .. import error


class BoolType(Type):
    """
    Represents a Bool ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BoolType):
            return False
        return True

    def __str__(self):
        return "bool"

    def byte_len(self):
        return 1

    def is_dynamic(self):
        return False

    def encode(self, value):
        """
        Encode a boolean value

        Args:
            value (bool): value to be encoded

        Returns:
            bytes: encoded bytes ("0x80" if True, "0x00" if False) of the boolean
        """
        assert isinstance(value, bool)
        if value:
            # True value is encoded as having a 1 on the most significant bit (0x80)
            return b"\x80"
        return b"\x00"

    def decode(self, bytestring):
        """
        Decodes a bytestring to a single boolean.

        Args:
            bytestring (bytes | bytearray): bytestring to be decoded that contains a single boolean, i.e. \x80 or \x00

        Returns:
            bool: boolean from the encoded bytestring
        """
        if (
            not (
                isinstance(bytestring, bytes)
                or isinstance(bytestring, bytearray)
            )
            or len(bytestring) != 1
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a bool: {}".format(
                    bytestring
                )
            )
        if bytestring == b"\x80":
            return True
        elif bytestring == b"\x00":
            return False
        else:
            raise error.ABIEncodingError(
                "boolean value could not be decoded: {}".format(bytestring)
            )
