from .base_type import BaseType, Type
from .. import error


class BoolType(Type):
    """
    Represents a Bool ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__(BaseType.Bool)

    def __eq__(self, other) -> bool:
        if not isinstance(other, BoolType):
            return False
        return self.abi_type_id == other.abi_type_id

    def __str__(self):
        return "bool"

    def byte_len(self):
        return 1

    def is_dynamic(self):
        return False

    def encode(self, value):
        assert isinstance(value, bool)
        if value:
            # True value is encoded as having a 1 on the most significant bit (0x80)
            return b"\x80"
        return b"\x00"

    def decode(self, bool_string):
        if (
            not (
                isinstance(bool_string, bytes)
                or isinstance(bool_string, bytearray)
            )
            or len(bool_string) != 1
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a bool: {}".format(
                    bool_string
                )
            )
        if bool_string.hex() == "80":
            return True
        elif bool_string.hex() == "00":
            return False
        else:
            raise error.ABIEncodingError(
                "boolean value could not be decoded: {}".format(bool_string)
            )
