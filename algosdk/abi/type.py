from abc import abstractmethod
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


class Type:
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

    def __str__(self):
        pass

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
        Deserialize the ABI value into a byte string using ABI encoding rules.
        """
        pass

    @staticmethod
    def type_from_string(s):
        """
        Convert a valid ABI string to a corresponding ABI type.
        """
        if s.endswith("[]"):
            array_arg_type = Type.type_from_string(s[:-2])
            return ArrayDynamicType(array_arg_type)
        elif s.endswith("]"):
            static_array_regex = "^([a-z\d\[\](),]+)\[([1-9][\d]*)]$"
            matches = re.search(static_array_regex, s)
            try:
                static_length = int(matches.group(2))
                array_type = Type.type_from_string(matches.group(1))
                return ArrayStaticType(array_type, static_length)
            except Exception as e:
                raise error.ABITypeError(
                    "malformed static array string: {}".format(s)
                ) from e
        elif s.startswith("uint"):
            try:
                if not s[4:].isdecimal():
                    raise error.ABITypeError(
                        "uint string does not contain a valid size: {}".format(
                            s
                        )
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
            tuples = TupleType.parse_tuple(s[1:-1])
            tuple_list = []
            for tup in tuples:
                if isinstance(tup, str):
                    tt = Type.type_from_string(str(tup))
                    tuple_list.append(tt)
                elif isinstance(tup, list):
                    tts = list(map(lambda t_: Type.type_from_string(t_), tup))
                    tuple_list.append(tts)
                else:
                    raise error.ABITypeError(
                        "cannot convert {} to an ABI type".format(tup)
                    )

            return TupleType(tuple_list)
        else:
            raise error.ABITypeError(
                "cannot convert {} to an ABI type".format(s)
            )


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
        return (value).to_bytes(self.bit_size, byteorder="big")

    def decode(self):
        pass


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

    def decode(self):
        pass


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
        assert isinstance(value, int)
        if value >= (2 ** self.bit_size) or value < 0:
            raise error.ABIEncodingError(
                "value {} is negative or is too big to fit in size {}".format(
                    value, self.bit_size
                )
            )
        return (value).to_bytes(self.bit_size, byteorder="big")

    def decode(self):
        pass


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

    def decode(self):
        pass


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
        child_types (list)
        static_length (int)
    """

    def __init__(self, arg_type, array_len) -> None:
        self.abi_type_id = BaseType.ArrayStatic
        self.child_type = arg_type
        self.child_types = list()
        self.static_length = array_len

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayStaticType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.child_type == other.child_type
            and self.child_types == other.child_types
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
        return any(child.is_dynamic() for child in self.child_types)

    def to_tuple(self):
        child_type_array = list()
        for _ in range(self.static_length):
            child_type_array.append(self.child_type)
        return TupleType(child_type_array)

    def encode(self, value_array):
        if len(value_array) != self.static_length:
            raise error.ABIEncodingError(
                "value array length does not match static array length: {}".format(
                    len(value_array)
                )
            )
        converted_tuple = self.to_tuple()
        return converted_tuple.encode(value_array)

    def decode(self):
        pass


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

    def to_tuple(self):
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
        converted_tuple = self.to_tuple()
        return converted_tuple.encode(value)

    def decode(self):
        pass


class ArrayDynamicType(Type):
    """
    Represents a ArrayDynamic ABI Type for encoding.

    Args:
        type_id (BaseType): type of ABI argument, as defined by the BaseType class above.
        child_type (Type): the type of the child_types array.

    Attributes:
        type_id (BaseType)
        child_type (Type)
        child_types (list)
    """

    def __init__(self, arg_type) -> None:
        self.abi_type_id = BaseType.ArrayDynamic
        self.child_type = arg_type
        self.child_types = list()

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayDynamicType):
            return False
        return (
            self.abi_type_id == other.abi_type_id
            and self.child_type == other.child_type
            and self.child_types == other.child_types
        )

    def __str__(self):
        return "{}[]".format(str(self.child_type))

    def byte_len(self):
        raise error.ABITypeError(
            "cannot get length of a dynamic type: {}".format(self.abi_type_id)
        )

    def is_dynamic(self):
        return True

    def to_tuple(self, value):
        child_type_array = [self.child_type] * len(value)
        return TupleType(child_type_array)

    def encode(self, value):
        converted_tuple = self.to_tuple(value)
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value)
        return bytearray(length_to_encode) + encoded

    def decode(self):
        pass


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

    def to_tuple(self, string_val):
        child_type_array = list()
        value_array = list()
        string_bytes = bytes(string_val, "utf-8")

        for val in string_bytes:
            child_type_array.append(ByteType())
            value_array.append((val.to_bytes(1, byteorder="big")))
        return (TupleType(child_type_array), value_array)

    def encode(self, string_val):
        converted_tuple, value = self.to_tuple(string_val)
        length_to_encode = len(converted_tuple.child_types).to_bytes(
            2, byteorder="big"
        )
        encoded = converted_tuple.encode(value)
        return length_to_encode + encoded

    def decode(self):
        pass


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
                after = TupleType.find_bool(self.child_types, i, 1)
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

    @staticmethod
    def find_bool(type_list, index, delta):
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

    def is_dynamic(self):
        return any(child.is_dynamic() for child in self.child_types)

    @staticmethod
    def parse_tuple(s):
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

    def compress_multiple_bool(value_list):
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
        if len(self.child_types) != len(tuple_elements):
            raise error.ABIEncodingError(
                "number of tuple elements do not match length of child types array"
            )

        # Create a head/tail component and use it to concat bytes later
        heads = list()
        tails = list()
        is_dynamic_index = dict()
        i = 0
        while i < len(tuple_elements):
            element = tuple_elements[i]
            if element.is_dynamic():
                # Head is not pre-determined for dynamic types; store a placeholder for now
                head_placeholder = bytes.fromhex("00")
                heads.append(None)
                is_dynamic_index[i] = True
                # if element.abi_type_id in (BaseType.ArrayDynamic, BaseType.Tuple):
                #     tail_encoding = element.encode(values)
                # else:
                tail_encoding = element.encode(values[i])
                tails.append(tail_encoding)
            else:
                if element.abi_type_id == BaseType.Bool:
                    before = self.find_bool(self.child_types, i, -1)
                    after = self.find_bool(self.child_types, i, 1)

                    # Pack bytes to heads and tails
                    if before % 8 != 0:
                        raise error.ABIEncodingError(
                            "expected before index should have number of bool mod 8 equal 0"
                        )
                    after = min(7, after)
                    compressed_int = TupleType.compress_multiple_bool(
                        values[i : i + after + 1]
                    )
                    # For converting one byte, the byteorder should not matter
                    heads.append((compressed_int).to_bytes(1, byteorder="big"))
                    i += after
                else:
                    # if element.abi_type_id in (BaseType.ArrayDynamic, BaseType.ArrayStatic, BaseType.Tuple):
                    #     encoded_tuple_element = element.encode(values)
                    # else:
                    encoded_tuple_element = element.encode(values[i])
                    heads.append(encoded_tuple_element)
                is_dynamic_index[i] = False
                tails.append(None)
            i += 1

        # Adjust heads for dynamic types
        head_length = 0
        for head_element in heads:
            if head_element:
                head_length += len(head_element)
            else:
                # Placeholder for a 2 byte length
                head_length += 2

        # Correctly encode dynamic types and replace placeholder
        tail_curr_length = 0
        for i in range(len(heads)):
            if i in is_dynamic_index and is_dynamic_index[i]:
                head_value = head_length + tail_curr_length
                if head_value >= 2 ** 16:
                    raise error.ABIEncodingError(
                        "byte length {} exceeds 2^16".format(head_value)
                    )
                heads[i] = head_value.to_bytes(2, byteorder="big")
            if tails[i]:
                tail_curr_length += len(tails[i])

        # Concatenate bytes
        encoded = bytearray()
        for head in heads:
            encoded += head
        for tail in tails:
            if tail:
                encoded += tail
        return encoded

    def decode(self):
        pass
