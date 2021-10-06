from .base_type import BaseType, Type
from .. import error


class ByteType(Type):
    """
    Represents a Byte ABI Type for encoding.
    """

    def __init__(self) -> None:
        self.abi_type_id = BaseType.Byte

    def __eq__(self, other) -> bool:
        if not isinstance(other, ByteType):
            return False
        return self.abi_type_id == other.abi_type_id

    def __str__(self):
        return "byte"

    def byte_len(self):
        return 1

    def is_dynamic(self):
        return False

    def encode(self, value):
        """
        Encode a single byte or a uint8
        """
        # Enforce ByteType to only accept bytes or int values
        if isinstance(value, bytes):
            value = int.from_bytes(value, byteorder="big")
        if not isinstance(value, int) or value < 0 or value > 255:
            raise error.ABIEncodingError(
                "value {} cannot be encoded into a byte".format(value)
            )
        return value.to_bytes(1, byteorder="big")

    def decode(self, byte_string):
        if (
            not (
                isinstance(byte_string, bytes)
                or isinstance(byte_string, bytearray)
            )
            or len(byte_string) != 1
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a byte: {}".format(
                    byte_string
                )
            )
        return int.from_bytes(byte_string, byteorder="big", signed=False)
