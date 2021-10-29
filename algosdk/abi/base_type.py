from abc import ABC, abstractmethod

# Globals
ABI_LENGTH_SIZE = 2  # We use 2 bytes to encode the length of a dynamic element


class Type(ABC):
    """
    Represents an ABI Type for encoding.
    """

    def __init__(
        self,
    ) -> None:
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def is_dynamic(self):
        """
        Return whether the ABI type is dynamic.
        """
        pass

    @abstractmethod
    def byte_len(self):
        """
        Return the length in bytes of the ABI type.
        """
        pass

    @abstractmethod
    def encode(self, value):
        """
        Serialize the ABI value into a byte string using ABI encoding rules.
        """
        pass

    @abstractmethod
    def decode(self, bytestring):
        """
        Deserialize the ABI type and value from a byte string using ABI encoding rules.
        """
        pass
