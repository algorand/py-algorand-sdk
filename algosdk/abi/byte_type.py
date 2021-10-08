from .base_type import Type
from .. import error


class ByteType(Type):
    """
    Represents a Byte ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, ByteType):
            return False
        return True

    def __str__(self):
        return "byte"

    def byte_len(self):
        return 1

    def is_dynamic(self):
        return False

    def encode(self, value):
        """
        Encode a single byte or a uint8

        Args:
            value (int): value to be encoded

        Returns:
            bytes: encoded bytes of the uint8
        """
        if not isinstance(value, int) or value < 0 or value > 255:
            raise error.ABIEncodingError(
                "value {} cannot be encoded into a byte".format(value)
            )
        return bytes([value])

    def decode(self, bytestring):
        """
        Decodes a bytestring to a single byte.

        Args:
            bytestring (bytes | bytearray): bytestring to be decoded

        Returns:
            bytes: byte of the encoded bytestring
        """
        if (
            not (
                isinstance(bytestring, bytes)
                or isinstance(bytestring, bytearray)
            )
            or len(bytestring) != 1
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a byte: {}".format(
                    bytestring
                )
            )
        return bytestring[0]
