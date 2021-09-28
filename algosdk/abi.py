from enum import IntEnum
import re
from unittest.mock import Base
from . import error


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
        child_types=list(),
        bit_size=None,
        precision=None,
        static_length=None,
    ) -> None:
        self.abi_type_id = type_id
        self.child_type = child_type  # Used for arrays
        self.child_types = child_types  # Used for tuples
        self.bit_size = bit_size
        self.precision = precision
        self.static_length = static_length

    def __str__(self):
        if self.abi_type_id == BaseType.Uint:
            return f"uint{str(self.bit_size)}"
        elif self.abi_type_id == BaseType.Byte:
            return f"byte"
        elif self.abi_type_id == BaseType.Ufixed:
            return f"ufixed{str(self.bit_size)}x{str(self.precision)}"
        elif self.abi_type_id == BaseType.Bool:
            return f"bool"
        elif self.abi_type_id == BaseType.ArrayStatic:
            return f"{str(self.child_type)}[{str(self.static_length)}]"
        elif self.abi_type_id == BaseType.Address:
            return f"address"
        elif self.abi_type_id == BaseType.ArrayDynamic:
            return f"{str(self.child_type)}[]"
        elif self.abi_type_id == BaseType.String:
            return f"string"
        elif self.abi_type_id == BaseType.Tuple:
            if not self.child_types:
                return f"()"
            return f"({','.join(str(t) for t in self.child_types)})"
        else:
            raise error.ABITypeError("failed to infer ABI type from id")

    def __eq__(self, other) -> bool:
        if (
            not isinstance(other, Type)
            or self.abi_type_id != other.abi_type_id
            or self.precision != other.precision
            or self.bit_size != other.bit_size
            or self.static_length != other.static_length
            or len(self.child_types) != len(other.child_types)
        ):
            return False
        for i in range(len(self.child_types)):
            if self.child_types[i] != other.child_types[i]:
                return False
        return True

    @staticmethod
    def make_uint_type(type_size):
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(f"unsupported uint bitSize: {type_size}")
        return Type(BaseType.Uint, bit_size=type_size)

    @staticmethod
    def make_byte_type():
        return Type(BaseType.Byte)

    @staticmethod
    def make_ufixed_type(type_size, type_precision):
        if (
            not isinstance(type_size, int)
            or type_size % 8 != 0
            or type_size < 8
            or type_size > 512
        ):
            raise error.ABITypeError(
                f"unsupported ufixed bitSize: {type_size}"
            )
        if (
            not isinstance(type_precision, int)
            or type_precision > 160
            or type_precision < 1
        ):
            raise error.ABITypeError(
                f"unsupported ufixed precision: {type_precision}"
            )
        return Type(
            BaseType.Ufixed, bit_size=type_size, precision=type_precision
        )

    @staticmethod
    def make_bool_type():
        return Type(BaseType.Bool)

    @staticmethod
    def make_static_array_type(arg_type, array_len):
        assert isinstance(arg_type, Type)
        return Type(
            BaseType.ArrayStatic,
            child_type=arg_type,
            child_types=list(),
            static_length=array_len,
        )

    @staticmethod
    def make_address_type():
        return Type(BaseType.Address)

    @staticmethod
    def make_dynamic_array_type(arg_type):
        assert isinstance(arg_type, Type)
        return Type(
            BaseType.ArrayDynamic, child_type=arg_type, child_types=list()
        )

    @staticmethod
    def make_string_type():
        return Type(BaseType.String)

    @staticmethod
    def make_tuple_type(arg_types):
        if len(arg_types) >= 2 ** 16:
            raise error.ABITypeError(f"tuple args exceed 2^16")
        assert isinstance(arg_types, list)
        return Type(
            BaseType.Tuple, child_types=arg_types, static_length=len(arg_types)
        )

    @staticmethod
    def type_from_string(s):
        if s.endswith("[]"):
            array_arg_type = Type.type_from_string(s[:-2])
            return Type.make_dynamic_array_type(array_arg_type)
        elif s.endswith("]"):
            static_array_regex = "^([a-z\d\[\](),]+)\[([1-9][\d]*)]$"
            matches = re.search(static_array_regex, s)
            try:
                static_length = int(matches.group(2))
                array_type = Type.type_from_string(matches.group(1))
                return Type.make_static_array_type(array_type, static_length)
            except:
                raise error.ABITypeError(f"malformed static array string: {s}")
        elif s.startswith("uint"):
            try:
                type_size = int(s[4:])
                return Type.make_uint_type(type_size)
            except:
                raise error.ABITypeError(f"malformed uint string: {s}")
        elif s == "byte":
            return Type.make_byte_type()
        elif s.startswith("ufixed"):
            ufixed_regex = "^ufixed([1-9][\d]*)x([1-9][\d]*)$"
            matches = re.search(ufixed_regex, s)
            try:
                bit_size = int(matches.group(1))
                precision = int(matches.group(2))
                return Type.make_ufixed_type(bit_size, precision)
            except:
                raise error.ABITypeError(f"malformed ufixed string: {s}")
        elif s == "bool":
            return Type.make_bool_type()
        elif s == "address":
            return Type.make_address_type()
        elif s == "string":
            return Type.make_string_type()
        elif len(s) >= 2 and s[0] == "(" and s[-1] == ")":
            # Recursively parse parentheses from a tuple string
            tuples = Type.parse_tuple(s[1:-1])
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
                        f"cannot convert {tup} to an ABI type"
                    )

            return Type.make_tuple_type(tuple_list)
        else:
            raise error.ABITypeError(f"cannot convert {s} to an ABI type")

    def parse_tuple(s):
        """
        Given a tuple string, parses one layer of the tuple.
        i.e. '(x,(y,(z)))' -> ['x', '(y,(z))']
        """
        # If the tuple content is empty, return an empty list
        if not s:
            return []

        if s.startswith(",") or s.endswith(","):
            raise error.ABITypeError(
                f"cannot have leading or trailing commas in {s}"
            )

        if ",," in s:
            raise error.ABITypeError(f"cannot have consecutive commas in {s}")

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
            raise error.ABITypeError(f"parenthesis mismatch: {s}")
        return tuple_strs

    def is_dynamic(self):
        """
        Returns whether the current type or any of its child types is a
        dynamic type or not.
        """
        if (
            self.abi_type_id == BaseType.ArrayDynamic
            or self.abi_type_id == BaseType.String
        ):
            return True
        for child in self.child_types:
            if child.is_dynamic():
                return True
        return False

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

    def byte_len(self):
        if self.abi_type_id == BaseType.Address:
            return 32
        elif self.abi_type_id == BaseType.Byte:
            return 1
        elif self.abi_type_id == BaseType.Bool:
            return 1
        elif (
            self.abi_type_id == BaseType.Uint
            or self.abi_type_id == BaseType.Ufixed
        ):
            return self.bit_size // 8
        elif self.abi_type_id == BaseType.ArrayStatic:
            if self.child_type.abi_type_id == BaseType.Bool:
                # 8 Boolean values can be encoded into 1 byte
                byte_length = self.static_length // 8
                if self.static_length % 8 != 0:
                    byte_length += 1
                return byte_length
            element_byte_length = self.child_type.byte_len()
            return self.static_length * element_byte_length
        elif self.abi_type_id == BaseType.Tuple:
            size = 0
            i = 0
            while i < len(self.child_types):
                if self.child_types[i].abi_type_id == BaseType.Bool:
                    after = Type.find_bool(self.child_types, i, 1)
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
        else:
            raise error.ABITypeError(
                f"cannot get length of a dynamic type: {self.abi_type_id}"
            )


class Value:
    def __init__(self, abi_type, val) -> None:
        self.abi_type = abi_type
        self.value = val

    @staticmethod
    def make_uint(value, size):
        assert isinstance(value, int)
        if value >= (2 ** size):
            raise error.ABIValueError(
                f"value {value} is too big to fit in size {size}"
            )
        return Value(Type.make_uint_type(size), value)

    @staticmethod
    def make_uint8(value):
        return Value.make_uint(value, 8)

    @staticmethod
    def make_uint16(value):
        return Value.make_uint(value, 16)

    @staticmethod
    def make_uint32(value):
        return Value.make_uint(value, 32)

    @staticmethod
    def make_uint64(value):
        return Value.make_uint(value, 64)

    @staticmethod
    def make_ufixed(value, size, precision):
        assert isinstance(value, int)
        ufixed_value_type = Type.make_ufixed_type(size, precision)
        uint_value = Value.make_uint(value, size)
        uint_value.abi_type = ufixed_value_type
        return uint_value

    @staticmethod
    def make_bool(value):
        assert isinstance(value, bool)
        return Value(Type.make_bool_type, value)

    @staticmethod
    def make_string(value):
        assert isinstance(value, str)
        return Value(Type.make_string_type, value)

    @staticmethod
    def make_byte(value):
        assert isinstance(value, bytes)
        return Value(Type.make_byte_type, value)

    @staticmethod
    def make_address(value):
        assert len(value) == 32
        return Value(Type.make_address_type, value)

    @staticmethod
    def make_dynamic_array(values, element_type):
        assert isinstance(values, list())
        assert isinstance(element_type, Type)
        if len(values) >= (2 ** 16):
            raise error.ABIValueError(
                f"dynamic array values length: {len(values)} must be less than uint16"
            )
        for val in values:
            assert isinstance(val, Value)
            if val.abi_type != element_type:
                raise error.ABIValueError(
                    f"dynamic array type mismatch: {val.abi_type} != {element_type}"
                )
        return Value(Type.make_dynamic_array_type(element_type), values)

    @staticmethod
    def make_static_array(values):
        assert isinstance(values, list())
        if len(values) >= (2 ** 16) or len(values) == 0:
            raise error.ABIValueError(
                f"dynamic array values length: {len(values)} must be greater than 0 and less than uint16"
            )
        for val in values:
            assert isinstance(val, Value)
            if val.abi_type != values[0].abi_type:
                raise error.ABIValueError(
                    f"dynamic array type mismatch: {val.abi_type} != {values[0].abi_type}"
                )
        return Value(
            Type.make_static_array_type(values[0].abi_type, len(values)),
            values,
        )

    @staticmethod
    def make_tuple(values):
        assert isinstance(values, list())
        if len(values) >= (2 ** 16):
            raise error.ABIValueError(
                f"tuple values length: {len(values)} must be less than uint16"
            )
        tuple_types = []
        for val in values:
            assert isinstance(val, Value)
            tuple_types.append(val.abi_type)

        return Value(Type.make_tuple_type(tuple_types), values)

    def get_uint(self):
        if not isinstance(self.abi_type.abi_type_id, BaseType.Uint):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a uint"
            )
        if self.value >= (2 ** self.abi_type.bit_size):
            raise error.ABIValueError(
                f"value {self.value} is too big to fit in size {self.abi_type.bit_size}"
            )
        return self.value

    def get_uint8(self):
        if (
            self.abi_type.abi_type_id != BaseType.Uint
            or self.abi_type.bit_size != 8
        ):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a uint8"
            )
        return self.get_uint()

    def get_uint16(self):
        if (
            self.abi_type.abi_type_id != BaseType.Uint
            or self.abi_type.bit_size != 16
        ):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a uint16"
            )
        return self.get_uint()

    def get_uint32(self):
        if (
            self.abi_type.abi_type_id != BaseType.Uint
            or self.abi_type.bit_size != 32
        ):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a uint32"
            )
        return self.get_uint()

    def get_uint64(self):
        if (
            self.abi_type.abi_type_id != BaseType.Uint
            or self.abi_type.bit_size != 64
        ):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a uint64"
            )
        return self.get_uint()

    def get_ufixed(self):
        if not isinstance(self.abi_type.abi_type_id, BaseType.Ufixed):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a ufixed"
            )
        if self.value >= (2 ** self.abi_type.bit_size) - 1:
            raise error.ABIValueError(
                f"value {self.value} is too big to fit in size {self.abi_type.bit_size}"
            )
        return self.value

    def get_bool(self):
        if not isinstance(self.abi_type.abi_type_id, BaseType.Bool):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a bool"
            )
        return self.value

    def get_string(self):
        if not isinstance(self.abi_type.abi_type_id, BaseType.String):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a string"
            )
        return self.value

    def get_byte(self):
        if not isinstance(self.abi_type.abi_type_id, BaseType.Byte):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not a byte"
            )
        return self.value

    def get_address(self):
        if not isinstance(self.abi_type.abi_type_id, BaseType.Address):
            raise error.ABIValueError(
                f"value type {self.abi_type.abi_type_id} is not an address"
            )
        return self.value

    def get_value_by_index(self, index):
        if isinstance(self.abi_type.abi_type_id, BaseType.ArrayDynamic):
            if index >= len(self.value):
                raise error.ABIValueError(
                    f"index {index} exceeds the length of array: {len(self.value)}"
                )
            return self.value[index]
        elif isinstance(
            self.abi_type.abi_type_id, BaseType.ArrayStatic
        ) or isinstance(self.abi_type.abi_type_id, BaseType.Tuple):
            if index >= self.abi_type.static_length:
                raise error.ABIValueError(
                    f"index {index} exceeds the length of array: {self.abi_type.static_length}"
                )
            return self.value[index]
        else:
            raise error.ABIValueError(
                f"cannot get value by index for {self.abi_type.abi_type_id} type"
            )
