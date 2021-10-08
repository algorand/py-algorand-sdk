from .base_type import ABI_LENGTH_SIZE, Type
from .byte_type import ByteType
from .tuple_type import TupleType
from .. import error


class ArrayDynamicType(Type):
    """
    Represents a ArrayDynamic ABI Type for encoding.

    Args:
        child_type (Type): the type of the dynamic array.

    Attributes:
        child_type (Type)
    """

    def __init__(self, arg_type) -> None:
        super().__init__()
        self.child_type = arg_type

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayDynamicType):
            return False
        return self.child_type == other.child_type

    def __str__(self):
        return "{}[]".format(self.child_type)

    def byte_len(self):
        raise error.ABITypeError(
            "cannot get length of a dynamic type: {}".format(self)
        )

    def is_dynamic(self):
        return True

    def _to_tuple_type(self, length):
        child_type_array = [self.child_type] * length
        return TupleType(child_type_array)

    def encode(self, value_array):
        """
        Encodes a list of values into a ArrayDynamic ABI bytestring.

        Args:
            value_array (list | bytes | bytearray): list of values to be encoded.
            If the child types are ByteType, then bytes or bytearray can be
            passed in to be encoded as well.

        Returns:
            bytes: encoded bytes of the dynamic array
        """
        if (
            isinstance(value_array, bytes)
            or isinstance(value_array, bytearray)
        ) and not isinstance(self.child_type, ByteType):
            raise error.ABIEncodingError(
                "cannot pass in bytes when the type of the array is not ByteType: {}".format(
                    value_array
                )
            )
        converted_tuple = self._to_tuple_type(len(value_array))
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value_array)
        return bytes(length_to_encode) + encoded

    def decode(self, array_bytes):
        """
        Decodes a bytestring to a dynamic list.

        Args:
            array_bytes (bytes | bytearray): bytestring to be decoded

        Returns:
            list: values from the encoded bytestring
        """
        if not (
            isinstance(array_bytes, bytearray)
            or isinstance(array_bytes, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(array_bytes)
            )
        if len(array_bytes) < ABI_LENGTH_SIZE:
            raise error.ABIEncodingError(
                "dynamic array is too short to be decoded: {}".format(
                    len(array_bytes)
                )
            )

        byte_length = int.from_bytes(
            array_bytes[:ABI_LENGTH_SIZE], byteorder="big"
        )
        converted_tuple = self._to_tuple_type(byte_length)
        return converted_tuple.decode(array_bytes[ABI_LENGTH_SIZE:])
