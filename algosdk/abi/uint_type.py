from typing import Union

from algosdk.abi.base_type import ABIType
from algosdk import error


class UintType(ABIType):
    """
    Represents an Uint ABI Type for encoding.

    Args:
        bit_size (int): size of a uint type, e.g. for a uint8, the bit_size is 8.

    Attributes:
        bit_size (int)
    """

    def __init__(self, type_size: int) -> None:
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(
                "unsupported uint bitSize: {}".format(type_size)
            )
        super().__init__()
        self.bit_size = type_size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UintType):
            return False
        return self.bit_size == other.bit_size

    def __str__(self) -> str:
        return "uint{}".format(self.bit_size)

    def byte_len(self) -> int:
        return self.bit_size // 8

    def is_dynamic(self) -> bool:
        return False

    def encode(self, value: int) -> bytes:
        """
        Encodes a value into a Uint ABI type bytestring.

        Args:
            value (int): uint value to be encoded

        Returns:
            bytes: encoded bytes of the uint value
        """
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

    def decode(self, bytestring: Union[bytes, bytearray]) -> int:
        """
        Decodes a bytestring to a uint.

        Args:
            bytestring (bytes | bytearray): bytestring to be decoded

        Returns:
            int: uint value from the encoded bytestring
        """
        if (
            not (
                isinstance(bytestring, bytes)
                or isinstance(bytestring, bytearray)
            )
            or len(bytestring) != self.bit_size // 8
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a uint{}: {}".format(
                    self.bit_size, bytestring
                )
            )
        # Convert bytes into an unsigned integer
        return int.from_bytes(bytestring, byteorder="big", signed=False)
