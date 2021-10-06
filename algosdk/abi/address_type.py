from .base_type import BaseType, Type
from .byte_type import ByteType
from .tuple_type import TupleType
from .. import error

from algosdk import encoding


class AddressType(Type):
    """
    Represents an Address ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__(BaseType.Address)

    def __eq__(self, other) -> bool:
        if not isinstance(other, AddressType):
            return False
        return self.abi_type_id == other.abi_type_id

    def __str__(self):
        return "address"

    def byte_len(self):
        return 32

    def is_dynamic(self):
        return False

    def _to_tuple_type(self):
        child_type_array = list()
        for _ in range(self.byte_len()):
            child_type_array.append(ByteType())
        return TupleType(child_type_array)

    def encode(self, value):
        """
        Encode an address string or a 32-byte public key
        """
        # Check that the value is an address in string or the public key in bytes
        if isinstance(value, str):
            try:
                value = encoding.decode_address(value)
            except Exception as e:
                raise error.ABIEncodingError(
                    "cannot encode the following address: {}".format(value)
                ) from e
        elif (
            not (isinstance(value, bytes) or isinstance(value, bytearray))
            or len(value) != 32
        ):
            raise error.ABIEncodingError(
                "cannot encode the following public key: {}".format(value)
            )
        converted_tuple = self._to_tuple_type()
        return converted_tuple.encode(value)

    def decode(self, addr_string):
        if (
            not (
                isinstance(addr_string, bytearray)
                or isinstance(addr_string, bytes)
            )
            or len(addr_string) != 32
        ):
            raise error.ABIEncodingError(
                "address string must be in bytes and correspond to a byte[32]: {}".format(
                    addr_string
                )
            )
        # Return the base32 encoded address string
        return encoding.encode_address(addr_string)
