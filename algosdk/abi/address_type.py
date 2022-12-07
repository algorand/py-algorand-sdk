from typing import Union, cast

from algosdk.abi.base_type import ABIType
from algosdk.abi.byte_type import ByteType
from algosdk.abi.tuple_type import TupleType
from algosdk import error

from algosdk import encoding


class AddressType(ABIType):
    """
    Represents an Address ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AddressType):
            return False
        return True

    def __str__(self) -> str:
        return "address"

    def byte_len(self) -> int:
        return 32

    def is_dynamic(self) -> bool:
        return False

    def _to_tuple_type(self):
        child_type_array = list()
        for _ in range(self.byte_len()):
            child_type_array.append(ByteType())
        return TupleType(child_type_array)

    def encode(self, value: Union[str, bytes]) -> bytes:
        """
        Encode an address string or a 32-byte public key into a Address ABI bytestring.

        Args:
            value (str | bytes): value to be encoded. It can be either a base32
            address string or a 32-byte public key.

        Returns:
            bytes: encoded bytes of the address
        """
        # Check that the value is an address in string or the public key in bytes
        if isinstance(value, str):
            try:
                value = encoding.decode_address(value)
            except Exception as e:
                raise error.ABIEncodingError(
                    f"cannot encode the following address: {value!r}"
                ) from e
        elif (
            not (isinstance(value, bytes) or isinstance(value, bytearray))
            or len(value) != 32
        ):
            raise error.ABIEncodingError(
                f"cannot encode the following public key: {value!r}"
            )
        value = cast(bytes, value)
        return bytes(value)

    def decode(self, bytestring: Union[bytearray, bytes]) -> str:
        """
        Decodes a bytestring to a base32 encoded address string.

        Args:
            bytestring (bytes | bytearray): bytestring to be decoded

        Returns:
            str: base32 encoded address from the encoded bytestring
        """
        if (
            not (
                isinstance(bytestring, bytearray)
                or isinstance(bytestring, bytes)
            )
            or len(bytestring) != 32
        ):
            raise error.ABIEncodingError(
                f"address string must be in bytes and correspond to a byte[32]: {bytestring!r}"
            )
        # Return the base32 encoded address string
        return encoding.encode_address(bytestring)
