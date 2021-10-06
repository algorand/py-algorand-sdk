from abc import ABC, abstractmethod
from enum import IntEnum

# Globals
ABI_LENGTH_SIZE = 2  # We use 2 bytes to encode the length of a dynamic element


class BaseType(IntEnum):
    Uint = 0
    Byte = 1
    Ufixed = 2
    Bool = 3
    ArrayStatic = 4
    Address = 5
    ArrayDynamic = 6
    String = 7
    Tuple = 8


class Type(ABC):
    """
    Represents an ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.

    Attributes:
        type_id (BaseType)
    """

    def __init__(
        self,
        type_id,
    ) -> None:
        self.abi_type_id = type_id

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def is_dynamic(self):
        """
        Return whether the ABI type is
        """
        pass

    @abstractmethod
    def byte_len(self):
        """
        Return the length is bytes of the ABI type.
        """
        pass

    @abstractmethod
    def encode(self, value):
        """
        Serialize the ABI value into a byte string using ABI encoding rules.
        """
        pass

    @abstractmethod
    def decode(self, value_string):
        """
        Deserialize the ABI type and value from a byte string using ABI encoding rules.
        """
        pass
