from .base_type import Type
from .. import error


class UfixedType(Type):
    """
    Represents an Ufixed ABI Type for encoding.

    Args:
        bit_size (int, optional): size of a ufixed type.
        precision (int, optional): number of precision for a ufixed type.

    Attributes:
        bit_size (int)
        precision (int)
    """

    def __init__(self, type_size, type_precision) -> None:
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(
                "unsupported ufixed bitSize: {}".format(type_size)
            )
        if (
            not isinstance(type_precision, int)
            or type_precision > 160
            or type_precision < 1
        ):
            raise error.ABITypeError(
                "unsupported ufixed precision: {}".format(type_precision)
            )
        super().__init__()
        self.bit_size = type_size
        self.precision = type_precision

    def __eq__(self, other) -> bool:
        if not isinstance(other, UfixedType):
            return False
        return (
            self.bit_size == other.bit_size
            and self.precision == other.precision
        )

    def __str__(self):
        return "ufixed{}x{}".format(self.bit_size, self.precision)

    def byte_len(self):
        return self.bit_size // 8

    def is_dynamic(self):
        return False

    def encode(self, value):
        """
        Encodes a value into a Ufixed ABI type bytestring. The precision denotes
        the denominator and the value denotes the numerator.

        Args:
            value (int): ufixed numerator value in uint to be encoded

        Returns:
            bytes: encoded bytes of the ufixed numerator
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

    def decode(self, value_string):
        """
        Decodes a bytestring to a ufixed numerator.

        Args:
            value_string (bytes | bytearray): bytestring to be decoded

        Returns:
            int: ufixed numerator value from the encoded bytestring
        """
        if (
            not (
                isinstance(value_string, bytes)
                or isinstance(value_string, bytearray)
            )
            or len(value_string) != self.bit_size // 8
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a ufixed{}x{}: {}".format(
                    self.bit_size, self.precision, value_string
                )
            )
        # Convert bytes into an unsigned integer numerator
        return int.from_bytes(value_string, byteorder="big", signed=False)
