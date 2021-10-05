from abc import ABC, abstractmethod
import math
import re

from enum import IntEnum

from algosdk import encoding
from .. import error


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


class UintType(Type):
    """
    Represents an Uint ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        bit_size (int, optional): size of a uint type, e.g. for a uint8, the bit_size is 8.

    Attributes:
        type_id (BaseType)
        bit_size (int)
    """

    def __init__(self, type_size) -> None:
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(
                "unsupported uint bitSize: {}".format(type_size)
            )
        self.abi_type_id = BaseType.Uint
        self.bit_size = type_size

    def __eq__(self, other) -> bool:
        if not isinstance(other, UintType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.bit_size == other.bit_size
        )

    def __str__(self):
        return "uint{}".format(str(self.bit_size))

    def byte_len(self):
        return self.bit_size // 8

    def is_dynamic(self):
        return False

    def encode(self, value):
        assert isinstance(value, int)
        if value >= (2 ** self.bit_size) or value < 0:
            raise error.ABIEncodingError(
                "value {} is negative or is too big to fit in size {}".format(
                    value, self.bit_size
                )
            )
        return (value).to_bytes(self.bit_size // 8, byteorder="big")

    def decode(self, value_string):
        if (
            not (
                isinstance(value_string, bytes)
                or isinstance(value_string, bytearray)
            )
            or len(value_string) != self.bit_size // 8
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a uint{}: {}".format(
                    self.bit_size, value_string
                )
            )
        # Convert bytes into an unsigned integer
        return int.from_bytes(value_string, byteorder="big", signed=False)


class ByteType(Type):
    """
    Represents a Byte ABI Type for encoding.
    """

    def __init__(self) -> None:
        self.abi_type_id = BaseType.Byte

    def __eq__(self, other) -> bool:
        if not isinstance(other, ByteType):
            return False
        return self.abi_type_id == other.abi_type_id

    def __str__(self):
        return "byte"

    def byte_len(self):
        return 1

    def is_dynamic(self):
        return False

    def encode(self, value):
        """
        Encode a single byte or a uint8
        """
        # Enforce ByteType to only accept bytes or int values
        if isinstance(value, bytes):
            value = int.from_bytes(value, byteorder="big")
        if not isinstance(value, int) or value < 0 or value > 255:
            raise error.ABIEncodingError(
                "value {} cannot be encoded into a byte".format(value)
            )
        return value.to_bytes(1, byteorder="big")

    def decode(self, byte_string):
        if (
            not (
                isinstance(byte_string, bytes)
                or isinstance(byte_string, bytearray)
            )
            or len(byte_string) != 1
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a byte: {}".format(
                    byte_string
                )
            )
        return int.from_bytes(byte_string, byteorder="big", signed=False)


class UfixedType(Type):
    """
    Represents an Ufixed ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        bit_size (int, optional): size of a ufixed type.
        precision (int, optional): number of precision for a ufixed type.

    Attributes:
        type_id (BaseType)
        bit_size (int)
        precision (int)
    """

    def __init__(self, type_size, type_precision) -> None:
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(
                "unsupported ufixed bitSize: {}".format(type_size)
            )
        if (
            not isinstance(type_precision, int)
            or type_precision > 160
            or type_precision < 1
        ):
            raise error.ABITypeError(
                "unsupported ufixed precision: {}".format(type_precision)
            )
        self.abi_type_id = BaseType.Ufixed
        self.bit_size = type_size
        self.precision = type_precision

    def __eq__(self, other) -> bool:
        if not isinstance(other, UfixedType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.bit_size == other.bit_size
            and self.precision == other.precision
        )

    def __str__(self):
        return "ufixed{}x{}".format(str(self.bit_size), str(self.precision))

    def byte_len(self):
        return self.bit_size // 8

    def is_dynamic(self):
        return False

    def encode(self, value):
        assert isinstance(value, int)
        if value >= (2 ** self.bit_size) or value < 0:
            raise error.ABIEncodingError(
                "value {} is negative or is too big to fit in size {}".format(
                    value, self.bit_size
                )
            )
        return (value).to_bytes(self.bit_size // 8, byteorder="big")

    def decode(self, value_string):
        if (
            not (
                isinstance(value_string, bytes)
                or isinstance(value_string, bytearray)
            )
            or len(value_string) != self.bit_size // 8
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a ufixed{}x{}: {}".format(
                    self.bit_size, self.precision, value_string
                )
            )
        # Convert bytes into an unsigned integer numerator
        return int.from_bytes(value_string, byteorder="big", signed=False)


class BoolType(Type):
    """
    Represents a Bool ABI Type for encoding.
    """

    def __init__(self) -> None:
        self.abi_type_id = BaseType.Bool

    def __eq__(self, other) -> bool:
        if not isinstance(other, BoolType):
            return False
        return self.abi_type_id == other.abi_type_id

    def __str__(self):
        return "bool"

    def byte_len(self):
        return 1

    def is_dynamic(self):
        return False

    def encode(self, value):
        assert isinstance(value, bool)
        if value:
            # True value is encoded as having a 1 on the most significant bit (0x80)
            return bytes.fromhex("80")
        return bytes.fromhex("00")

    def decode(self, bool_string):
        if (
            not (
                isinstance(bool_string, bytes)
                or isinstance(bool_string, bytearray)
            )
            or len(bool_string) != 1
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes and correspond to a bool: {}".format(
                    bool_string
                )
            )
        if bool_string.hex() == "80":
            return True
        elif bool_string.hex() == "00":
            return False
        else:
            raise error.ABIEncodingError(
                "boolean value could not be decoded: {}".format(bool_string)
            )


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
        self.abi_type_id = BaseType.ArrayStatic
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
        return "{}[{}]".format(str(self.child_type), str(self.static_length))

    def byte_len(self):
        if self.child_type.abi_type_id == BaseType.Bool:
            # 8 Boolean values can be encoded into 1 byte
            return math.ceil(self.static_length / 8)
        element_byte_length = self.child_type.byte_len()
        return self.static_length * element_byte_length

    def is_dynamic(self):
        return self.child_type.is_dynamic()

    def _to_tuple(self):
        child_type_array = [self.child_type] * self.static_length
        return TupleType(child_type_array)

    def encode(self, value_array):
        if len(value_array) != self.static_length:
            raise error.ABIEncodingError(
                "value array length does not match static array length: {}".format(
                    len(value_array)
                )
            )
        converted_tuple = self._to_tuple()
        return converted_tuple.encode(value_array)

    def decode(self, array_bytes):
        if not (
            isinstance(array_bytes, bytearray)
            or isinstance(array_bytes, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(array_bytes)
            )
        converted_tuple = self._to_tuple()
        return converted_tuple.decode(array_bytes)


class AddressType(Type):
    """
    Represents an Address ABI Type for encoding.
    """

    def __init__(self) -> None:
        self.abi_type_id = BaseType.Address

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

    def _to_tuple(self):
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
                )
        elif not isinstance(value, bytes) or len(value) != 32:
            raise error.ABIEncodingError(
                "cannot encode the following public key: {}".format(value)
            )
        converted_tuple = self._to_tuple()
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
        return addr_string


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
        self.abi_type_id = BaseType.ArrayDynamic
        self.child_type = arg_type

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayDynamicType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.child_type == other.child_type
        )

    def __str__(self):
        return "{}[]".format(str(self.child_type))

    def byte_len(self):
        raise error.ABITypeError(
            "cannot get length of a dynamic type: {}".format(self.abi_type_id)
        )

    def is_dynamic(self):
        return True

    def _to_tuple(self, length):
        child_type_array = [self.child_type] * length
        return TupleType(child_type_array)

    def encode(self, value):
        converted_tuple = self._to_tuple(len(value))
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value)
        return bytearray(length_to_encode) + encoded

    def decode(self, array_bytes):
        length_byte_size = (
            2  # We use 2 bytes to encode the length of a dynamic element
        )
        if not (
            isinstance(array_bytes, bytearray)
            or isinstance(array_bytes, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(array_bytes)
            )
        if len(array_bytes) < length_byte_size:
            raise error.ABIEncodingError(
                "dynamic array is too short to be decoded: {}".format(
                    len(array_bytes)
                )
            )

        byte_length = int.from_bytes(
            array_bytes[:length_byte_size], byteorder="big"
        )
        converted_tuple = self._to_tuple(byte_length)
        return converted_tuple.decode(array_bytes[length_byte_size:])


class StringType(Type):
    """
    Represents a String ABI Type for encoding.
    """

    def __init__(self) -> None:
        self.abi_type_id = BaseType.String

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

    def _to_tuple(self, string_val):
        child_type_array = list()
        value_array = list()
        string_bytes = bytes(string_val, "utf-8")

        for val in string_bytes:
            child_type_array.append(ByteType())
            value_array.append((val.to_bytes(1, byteorder="big")))
        return (TupleType(child_type_array), value_array)

    def encode(self, string_val):
        converted_tuple, value = self._to_tuple(string_val)
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value)
        return length_to_encode + encoded

    def decode(self, byte_string):
        length_byte_size = (
            2  # We use 2 bytes to encode the length of a dynamic element
        )
        if not (
            isinstance(byte_string, bytearray)
            or isinstance(byte_string, bytes)
        ):
            raise error.ABIEncodingError(
                "value to be decoded must be in bytes: {}".format(byte_string)
            )
        if len(byte_string) < length_byte_size:
            raise error.ABIEncodingError(
                "string is too short to be decoded: {}".format(
                    len(byte_string)
                )
            )
        byte_length = int.from_bytes(
            byte_string[:length_byte_size], byteorder="big"
        )
        if len(byte_string[length_byte_size:]) != byte_length:
            raise error.ABIEncodingError(
                "string length byte does not match actual length of string: {} != {}".format(
                    len(byte_string[length_byte_size:]), byte_length
                )
            )
        return (byte_string[length_byte_size:]).decode("utf-8")


class TupleType(Type):
    """
    Represents a Tuple ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        child_type (Type): the type of the child_types array.

    Attributes:
        type_id (BaseType)
        child_types (list)
        static_length (int)
    """

    def __init__(self, arg_types) -> None:
        if len(arg_types) >= 2 ** 16:
            raise error.ABITypeError(
                "tuple args cannot exceed a uint16: {}".format(len(arg_types))
            )
        self.abi_type_id = BaseType.Tuple
        self.child_types = arg_types
        self.static_length = len(arg_types)

    def __eq__(self, other) -> bool:
        if not isinstance(other, TupleType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.child_types == other.child_types
            and self.static_length == other.static_length
        )

    def __str__(self):
        return "({})".format(",".join(str(t) for t in self.child_types))

    def byte_len(self):
        size = 0
        i = 0
        while i < len(self.child_types):
            if self.child_types[i].abi_type_id == BaseType.Bool:
                after = TupleType._find_bool(self.child_types, i, 1)
                i += after
                bool_num = after + 1
                size += bool_num // 8
                if bool_num % 8 != 0:
                    size += 1
            else:
                child_byte_size = self.child_types[i].byte_len()
                size += child_byte_size
            i += 1
        return size

    def is_dynamic(self):
        return any(child.is_dynamic() for child in self.child_types)

    @staticmethod
    def _find_bool(type_list, index, delta):
        """
        Helper function to find consecutive booleans from current index in a tuple.
        """
        until = 0
        while True:
            curr = index + delta * until
            if type_list[curr].abi_type_id == BaseType.Bool:
                if curr != len(type_list) - 1 and delta > 0:
                    until += 1
                elif curr > 0 and delta < 0:
                    until += 1
                else:
                    break
            else:
                until -= 1
                break
        return until

    @staticmethod
    def _parse_tuple(s):
        """
        Given a tuple string, parses one layer of the tuple and returns tokens as a list.
        i.e. 'x,(y,(z))' -> ['x', '(y,(z))']
        """
        # If the tuple content is empty, return an empty list
        if not s:
            return []

        if s.startswith(",") or s.endswith(","):
            raise error.ABITypeError(
                "cannot have leading or trailing commas in {}".format(s)
            )

        if ",," in s:
            raise error.ABITypeError(
                "cannot have consecutive commas in {}".format(s)
            )

        tuple_strs = []
        depth = 0
        word = ""
        for char in s:
            word += char
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == ",":
                # If the comma is at depth 0, put the word as a new token.
                if depth == 0:
                    word = word[:-1]
                    if word:
                        tuple_strs.append(word)
                        word = ""
        if word:
            tuple_strs.append(word)
        if depth != 0:
            raise error.ABITypeError("parenthesis mismatch: {}".format(s))
        return tuple_strs

    @staticmethod
    def _compress_multiple_bool(value_list):
        """
        Compress consecutive boolean values into a byte for a Tuple/Array.
        """
        result = 0
        if len(value_list) > 8:
            raise error.ABIEncodingError(
                "length of list should not be greater than 8"
            )
        for i, value in enumerate(value_list):
            assert isinstance(value, bool)
            bool_val = value
            if bool_val:
                result |= 1 << (7 - i)
        return result

    def encode(self, values):
        if len(self.child_types) >= (2 ** 16):
            raise error.ABIEncodingError(
                "length of tuple array exceeds 2^16: {}".format(
                    len(self.child_types)
                )
            )
        tuple_elements = self.child_types

        # Create a head/tail component and use it to concat bytes later
        heads = list()
        tails = list()
        is_dynamic_index = list()
        i = 0
        length_byte_size = (
            2  # We use 2 bytes to encode the length of a dynamic element
        )
        while i < len(tuple_elements):
            element = tuple_elements[i]
            if element.is_dynamic():
                # Head is not pre-determined for dynamic types; store a placeholder for now
                heads.append(None)
                is_dynamic_index.append(True)
                tail_encoding = element.encode(values[i])
                tails.append(tail_encoding)
            else:
                if element.abi_type_id == BaseType.Bool:
                    before = TupleType._find_bool(self.child_types, i, -1)
                    after = TupleType._find_bool(self.child_types, i, 1)

                    # Pack bytes to heads and tails
                    if before % 8 != 0:
                        raise error.ABIEncodingError(
                            "expected before index should have number of bool mod 8 equal 0"
                        )
                    after = min(7, after)
                    compressed_int = TupleType._compress_multiple_bool(
                        values[i : i + after + 1]
                    )
                    # For converting one byte, the byteorder should not matter
                    heads.append((compressed_int).to_bytes(1, byteorder="big"))
                    i += after
                else:
                    encoded_tuple_element = element.encode(values[i])
                    heads.append(encoded_tuple_element)
                is_dynamic_index.append(False)
                tails.append(None)
            i += 1

        # Adjust heads for dynamic types
        head_length = 0
        for head_element in heads:
            if head_element:
                head_length += len(head_element)
            else:
                # Placeholder for a 2 byte length encoding
                head_length += length_byte_size

        # Correctly encode dynamic types and replace placeholder
        tail_curr_length = 0
        for i in range(len(heads)):
            if is_dynamic_index[i]:
                head_value = head_length + tail_curr_length
                if head_value >= 2 ** 16:
                    raise error.ABIEncodingError(
                        "byte length {} exceeds 2^16".format(head_value)
                    )
                heads[i] = head_value.to_bytes(
                    length_byte_size, byteorder="big"
                )
            if tails[i]:
                tail_curr_length += len(tails[i])

        # Concatenate bytes
        encoded = bytearray()
        for head in heads:
            if head:
                encoded += head
        for tail in tails:
            if tail:
                encoded += tail
        return encoded

    def decode(self, tuple_string):
        if not (
            isinstance(tuple_string, bytes)
            or isinstance(tuple_string, bytearray)
        ):
            raise error.ABIEncodingError(
                "value string must be in bytes: {}".format(tuple_string)
            )
        tuple_elements = self.child_types
        dynamic_segments = (
            list()
        )  # Store the start and end of a dynamic element
        value_partitions = list()
        i = 0
        array_index = 0
        length_byte_size = (
            2  # We use 2 bytes to encode the length of a dynamic element
        )

        while i < len(tuple_elements):
            element = tuple_elements[i]
            if element.is_dynamic():
                if len(tuple_string[array_index:]) < length_byte_size:
                    raise error.ABIEncodingError(
                        "malformed value: dynamically typed values must contain a two-byte length specifier"
                    )
                # Decode the size of the dynamic element
                dynamic_index = int.from_bytes(
                    tuple_string[array_index : array_index + length_byte_size],
                    byteorder="big",
                    signed=False,
                )
                if len(dynamic_segments) > 0:
                    dynamic_segments[len(dynamic_segments) - 1][
                        1
                    ] = dynamic_index
                    # Check that the right side of segment is greater than the left side
                    assert (
                        dynamic_index
                        > dynamic_segments[len(dynamic_segments) - 1][0]
                    )
                # Since we do not know where the current dynamic element ends, put a placeholder and update later
                dynamic_segments.append([dynamic_index, -1])
                value_partitions.append(None)
                array_index += length_byte_size
            else:
                if element.abi_type_id == BaseType.Bool:
                    before = TupleType._find_bool(self.child_types, i, -1)
                    after = TupleType._find_bool(self.child_types, i, 1)

                    if before % 8 != 0:
                        raise error.ABIEncodingError(
                            "expected before index should have number of bool mod 8 equal 0"
                        )
                    after = min(7, after)
                    # Parse bool values into multiple byte strings
                    for bool_i in range(after + 1):
                        mask = 128 >> bool_i
                        bit = int.from_bytes(
                            tuple_string[array_index : array_index + 1],
                            byteorder="big",
                        )
                        if mask & bit:
                            value_partitions.append(bytes.fromhex("80"))
                        else:
                            value_partitions.append(bytes.fromhex("00"))
                    i += after
                    array_index += 1
                else:
                    curr_len = element.byte_len()
                    value_partitions.append(
                        tuple_string[array_index : array_index + curr_len]
                    )
                    array_index += curr_len
            if (
                array_index >= len(tuple_string)
                and i != len(tuple_elements) - 1
            ):
                raise error.ABIEncodingError(
                    "input string is not long enough to be decoded: {}".format(
                        tuple_string
                    )
                )
            i += 1

        if len(dynamic_segments) > 0:
            dynamic_segments[len(dynamic_segments) - 1][1] = len(tuple_string)
            array_index = len(tuple_string)
        if array_index < len(tuple_string):
            raise error.ABIEncodingError(
                "input string was not fully consumed: {}".format(tuple_string)
            )

        # Check dynamic element partitions
        segment_index = 0
        for i, element in enumerate(tuple_elements):
            if element.is_dynamic():
                value_partitions[i] = tuple_string[
                    dynamic_segments[segment_index][0] : dynamic_segments[
                        segment_index
                    ][1]
                ]
                segment_index += 1

        # Decode individual tuple elements
        values = list()
        for i, element in enumerate(tuple_elements):
            val = element.decode(value_partitions[i])
            values.append(val)
        return values


def type_from_string(s):
    """
    Convert a valid ABI string to a corresponding ABI type.
    """
    if s.endswith("[]"):
        array_arg_type = type_from_string(s[:-2])
        return ArrayDynamicType(array_arg_type)
    elif s.endswith("]"):
        static_array_regex = "^([a-z\d\[\](),]+)\[([1-9][\d]*)]$"
        matches = re.search(static_array_regex, s)
        try:
            static_length = int(matches.group(2))
            array_type = type_from_string(matches.group(1))
            return ArrayStaticType(array_type, static_length)
        except Exception as e:
            raise error.ABITypeError(
                "malformed static array string: {}".format(s)
            ) from e
    elif s.startswith("uint"):
        try:
            if not s[4:].isdecimal():
                raise error.ABITypeError(
                    "uint string does not contain a valid size: {}".format(s)
                )
            type_size = int(s[4:])
            return UintType(type_size)
        except Exception as e:
            raise error.ABITypeError(
                "malformed uint string: {}".format(s)
            ) from e
    elif s == "byte":
        return ByteType()
    elif s.startswith("ufixed"):
        ufixed_regex = "^ufixed([1-9][\d]*)x([1-9][\d]*)$"
        matches = re.search(ufixed_regex, s)
        try:
            bit_size = int(matches.group(1))
            precision = int(matches.group(2))
            return UfixedType(bit_size, precision)
        except Exception as e:
            raise error.ABITypeError(
                "malformed ufixed string: {}".format(s)
            ) from e
    elif s == "bool":
        return BoolType()
    elif s == "address":
        return AddressType()
    elif s == "string":
        return StringType()
    elif len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        # Recursively parse parentheses from a tuple string
        tuples = TupleType._parse_tuple(s[1:-1])
        tuple_list = []
        for tup in tuples:
            if isinstance(tup, str):
                tt = type_from_string(tup)
                tuple_list.append(tt)
            elif isinstance(tup, list):
                tts = [type_from_string(t_) for t_ in tup]
                tuple_list.append(tts)
            else:
                raise error.ABITypeError(
                    "cannot convert {} to an ABI type".format(tup)
                )

        return TupleType(tuple_list)
    else:
        raise error.ABITypeError("cannot convert {} to an ABI type".format(s))
