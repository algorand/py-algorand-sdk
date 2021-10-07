from .base_type import ABI_LENGTH_SIZE, BaseType, Type
from .. import error


class StringType(Type):
    """
    Represents a String ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__(BaseType.String)

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

    def encode(self, string_val):
        """
        Encode a value into a String ABI bytestring.

        Args:
            value (str | bytes): value to be encoded. It can be either a base32
            address string or a 32-byte public key.

        Returns:
            bytes: encoded bytes of the uint8
        """
        length_to_encode = len(string_val).to_bytes(2, byteorder="big")
        encoded = string_val.encode("utf-8")
        return length_to_encode + encoded

    def decode(self, byte_string):
        """
        Decodes a bytestring to a string.

        Args:
            byte_string (bytes | bytearray): bytestring to be decoded

        Returns:
            str: string from the encoded bytestring
        """
        if not (
            isinstance(byte_string, bytearray)
            or isinstance(byte_string, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(byte_string)
            )
        if len(byte_string) < ABI_LENGTH_SIZE:
            raise error.ABIEncodingError(
                "string is too short to be decoded: {}".format(
                    len(byte_string)
                )
            )
        byte_length = int.from_bytes(
            byte_string[:ABI_LENGTH_SIZE], byteorder="big"
        )
        if len(byte_string[ABI_LENGTH_SIZE:]) != byte_length:
            raise error.ABIEncodingError(
                "string length byte does not match actual length of string: {} != {}".format(
                    len(byte_string[ABI_LENGTH_SIZE:]), byte_length
                )
            )
        return (byte_string[ABI_LENGTH_SIZE:]).decode("utf-8")
