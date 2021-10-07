from .base_type import BaseType, Type
from .. import error


class UintType(Type):
    """
    Represents an Uint ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        bit_size (int, optional): size of a uint type, e.g. for a uint8, the bit_size is 8.

    Attributes:
        type_id (BaseType)
        bit_size (int)
    """

    def __init__(self, type_size) -> None:
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(
                "unsupported uint bitSize: {}".format(type_size)
            )
        super().__init__(BaseType.Uint)
        self.bit_size = type_size

    def __eq__(self, other) -> bool:
        if not isinstance(other, UintType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.bit_size == other.bit_size
        )

    def __str__(self):
        return "uint{}".format(self.bit_size)

    def byte_len(self):
        return self.bit_size // 8

    def is_dynamic(self):
        return False

    def encode(self, value):
        """
        Encodes a value into a Uint ABI type bytestring.

        Args:
            value (int): uint value to be encoded

        Returns:
            bytes: encoded bytes of the uint value
        """
        assert isinstance(value, int)
        if (
            not isinstance(value, int)
            or value >= (2 ** self.bit_size)
            or value < 0
        ):
            raise error.ABIEncodingError(
                "value {} is not a non-negative int or is too big to fit in size {}".format(
                    value, self.bit_size
                )
            )
        return value.to_bytes(self.bit_size // 8, byteorder="big")

    def decode(self, value_string):
        """
        Decodes a bytestring to a uint.

        Args:
            value_string (bytes | bytearray): bytestring to be decoded

        Returns:
            int: uint value from the encoded bytestring
        """
        if (
            not (
                isinstance(value_string, bytes)
                or isinstance(value_string, bytearray)
            )
            or len(value_string) != self.bit_size // 8
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a uint{}: {}".format(
                    self.bit_size, value_string
                )
            )
        # Convert bytes into an unsigned integer
        return int.from_bytes(value_string, byteorder="big", signed=False)
