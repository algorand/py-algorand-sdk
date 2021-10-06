from abc import ABC, abstractmethod
from enum import IntEnum


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
        child_type (Type, optional): the type of the child_types array.
        child_types (list, optional): list of types of the children for a tuple.
        bit_size (int, optional): size of a uint/ufixed type, e.g. for a uint8, the bit_size is 8.
        precision (int, optional): number of precision for a ufixed type.
        static_length (int, optional): index of the asset

    Attributes:
        type_id (BaseType)
        child_type (Type)
        child_types (list)
        bit_size (int)
        precision (int)
        static_length (int)
    """

    def __init__(
        self,
        type_id,
        child_type=None,
        child_types=None,
        bit_size=None,
        precision=None,
        static_length=None,
    ) -> None:
        self.abi_type_id = type_id
        self.child_type = child_type  # Used for arrays
        if not child_types:
            self.child_types = list()
        else:
            self.child_types = child_types  # Used for tuples
        self.bit_size = bit_size
        self.precision = precision
        self.static_length = static_length

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
    def encode(self):
        """
        Serialize the ABI value into a byte string using ABI encoding rules.
        """
        pass

    @abstractmethod
    def decode(self):
        """
        Deserialize the ABI type and value from a byte string using ABI encoding rules.
        """
        pass
