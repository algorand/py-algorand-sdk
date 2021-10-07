import math

from .base_type import BaseType, Type
from .tuple_type import TupleType
from .. import error


class ArrayStaticType(Type):
    """
    Represents a ArrayStatic ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        child_type (Type): the type of the child_types array.
        static_length (int): index of the asset

    Attributes:
        type_id (BaseType)
        child_type (Type)
        static_length (int)
    """

    def __init__(self, arg_type, array_len) -> None:
        super().__init__(BaseType.ArrayStatic)
        self.child_type = arg_type
        self.static_length = array_len

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayStaticType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.child_type == other.child_type
            and self.static_length == other.static_length
        )

    def __str__(self):
        return "{}[{}]".format(self.child_type, self.static_length)

    def byte_len(self):
        if self.child_type.abi_type_id == BaseType.Bool:
            # 8 Boolean values can be encoded into 1 byte
            return math.ceil(self.static_length / 8)
        element_byte_length = self.child_type.byte_len()
        return self.static_length * element_byte_length

    def is_dynamic(self):
        return self.child_type.is_dynamic()

    def _to_tuple_type(self):
        child_type_array = [self.child_type] * self.static_length
        return TupleType(child_type_array)

    def encode(self, value_array):
        """
        Encodes a list of values into a ArrayStatic ABI bytestring.

        Args:
            value_array (list | bytes | bytearray): list of values to be encoded.
            The number of elements must match the predefined length of array.
            If the child types are ByteType, then bytes or bytearray can be
            passed in to be encoded as well.

        Returns:
            bytes: encoded bytes of the static array
        """
        if len(value_array) != self.static_length:
            raise error.ABIEncodingError(
                "value array length does not match static array length: {}".format(
                    len(value_array)
                )
            )
        if (
            isinstance(value_array, bytes)
            or isinstance(value_array, bytearray)
        ) and self.child_type.abi_type_id != BaseType.Byte:
            raise error.ABIEncodingError(
                "cannot pass in bytes when the type of the array is not ByteType: {}".format(
                    value_array
                )
            )
        converted_tuple = self._to_tuple_type()
        return converted_tuple.encode(value_array)

    def decode(self, array_bytes):
        """
        Decodes a bytestring to a static list.

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
        converted_tuple = self._to_tuple_type()
        return converted_tuple.decode(array_bytes)
