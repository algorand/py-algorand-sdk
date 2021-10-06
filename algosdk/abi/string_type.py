from .base_type import BaseType, Type
from .byte_type import ByteType
from .tuple_type import TupleType
from .. import error


class StringType(Type):
    """
    Represents a String ABI Type for encoding.
    """

    def __init__(self) -> None:
        self.abi_type_id = BaseType.String

    def __eq__(self, other) -> bool:
        if not isinstance(other, StringType):
            return False
        return self.abi_type_id == other.abi_type_id

    def __str__(self):
        return "string"

    def byte_len(self):
        raise error.ABITypeError(
            "cannot get length of a dynamic type: {}".format(self.abi_type_id)
        )

    def is_dynamic(self):
        return True

    def _to_tuple_type(self, string_val):
        child_type_array = list()
        value_array = list()
        string_bytes = bytes(string_val, "utf-8")

        for val in string_bytes:
            child_type_array.append(ByteType())
            value_array.append((val.to_bytes(1, byteorder="big")))
        return (TupleType(child_type_array), value_array)

    def encode(self, string_val):
        converted_tuple, value = self._to_tuple_type(string_val)
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value)
        return length_to_encode + encoded

    def decode(self, byte_string):
        length_byte_size = (
            2  # We use 2 bytes to encode the length of a dynamic element
        )
        if not (
            isinstance(byte_string, bytearray)
            or isinstance(byte_string, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(byte_string)
            )
        if len(byte_string) < length_byte_size:
            raise error.ABIEncodingError(
                "string is too short to be decoded: {}".format(
                    len(byte_string)
                )
            )
        byte_length = int.from_bytes(
            byte_string[:length_byte_size], byteorder="big"
        )
        if len(byte_string[length_byte_size:]) != byte_length:
            raise error.ABIEncodingError(
                "string length byte does not match actual length of string: {} != {}".format(
                    len(byte_string[length_byte_size:]), byte_length
                )
            )
        return (byte_string[length_byte_size:]).decode("utf-8")
