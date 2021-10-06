from .base_type import BaseType, Type
from .. import error


class UfixedType(Type):
    """
    Represents an Ufixed ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        bit_size (int, optional): size of a ufixed type.
        precision (int, optional): number of precision for a ufixed type.

    Attributes:
        type_id (BaseType)
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
        super().__init__(BaseType.Ufixed)
        self.bit_size = type_size
        self.precision = type_precision

    def __eq__(self, other) -> bool:
        if not isinstance(other, UfixedType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.bit_size == other.bit_size
            and self.precision == other.precision
        )

    def __str__(self):
        return "ufixed{}x{}".format(self.bit_size, self.precision)

    def byte_len(self):
        return self.bit_size // 8

    def is_dynamic(self):
        return False

    def encode(self, value):
        assert isinstance(value, int)
        if value >= (2 ** self.bit_size) or value < 0:
            raise error.ABIEncodingError(
                "value {} is negative or is too big to fit in size {}".format(
                    value, self.bit_size
                )
            )
        return value.to_bytes(self.bit_size // 8, byteorder="big")

    def decode(self, value_string):
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
