from .base_type import ABI_LENGTH_SIZE, BaseType, Type
from .tuple_type import TupleType
from .. import error


class ArrayDynamicType(Type):
    """
    Represents a ArrayDynamic ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        child_type (Type): the type of the dynamic array.

    Attributes:
        type_id (BaseType)
        child_type (Type)
    """

    def __init__(self, arg_type) -> None:
        super().__init__(BaseType.ArrayDynamic)
        self.child_type = arg_type

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayDynamicType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.child_type == other.child_type
        )

    def __str__(self):
        return "{}[]".format(self.child_type)

    def byte_len(self):
        raise error.ABITypeError(
            "cannot get length of a dynamic type: {}".format(self.abi_type_id)
        )

    def is_dynamic(self):
        return True

    def _to_tuple_type(self, length):
        child_type_array = [self.child_type] * length
        return TupleType(child_type_array)

    def encode(self, value):
        converted_tuple = self._to_tuple_type(len(value))
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value)
        return bytearray(length_to_encode) + encoded

    def decode(self, array_bytes):
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
