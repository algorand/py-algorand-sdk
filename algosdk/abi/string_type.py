from typing import NoReturn, Union

from algosdk.abi.base_type import ABI_LENGTH_SIZE, ABIType
from algosdk import error


class StringType(ABIType):
    """
    Represents a String ABI Type for encoding.
    """

    def __init__(self) -> None:
        super().__init__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StringType):
            return False
        return True

    def __str__(self) -> str:
        return "string"

    def byte_len(self) -> NoReturn:
        raise error.ABITypeError(
            "cannot get length of a dynamic type: {}".format(self)
        )

    def is_dynamic(self) -> bool:
        return True

    def encode(self, string_val: str) -> bytes:
        """
        Encode a value into a String ABI bytestring.

        Args:
            value (str): string to be encoded.

        Returns:
            bytes: encoded bytes of the string
        """
        encoded = string_val.encode("utf-8")
        length_to_encode = len(encoded).to_bytes(2, byteorder="big")
        return length_to_encode + encoded

    def decode(self, bytestring: Union[bytes, bytearray]) -> str:
        """
        Decodes a bytestring to a string.

        Args:
            bytestring (bytes | bytearray): bytestring to be decoded

        Returns:
            str: string from the encoded bytestring
        """
        if not (
            isinstance(bytestring, bytearray) or isinstance(bytestring, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(bytestring)
            )
        if len(bytestring) < ABI_LENGTH_SIZE:
            raise error.ABIEncodingError(
                "string is too short to be decoded: {}".format(len(bytestring))
            )
        byte_length = int.from_bytes(
            bytestring[:ABI_LENGTH_SIZE], byteorder="big"
        )
        if len(bytestring[ABI_LENGTH_SIZE:]) != byte_length:
            raise error.ABIEncodingError(
                "string length byte does not match actual length of string: {} != {}".format(
                    len(bytestring[ABI_LENGTH_SIZE:]), byte_length
                )
            )
        return (bytestring[ABI_LENGTH_SIZE:]).decode("utf-8")
