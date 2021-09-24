from enum import IntEnum
import re
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
        self.child_type = child_type  # Type of child_types array
        self.child_types = child_types  # List of Type
        self.bit_size = bit_size  # uint16
        self.precision = precision  # uint16
        self.static_length = static_length  # uint16

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
            return f"{self.child_type}[{str(self.static_length)}]"
        elif self.abi_type_id == BaseType.Address:
            return f"address"
        elif self.abi_type_id == BaseType.ArrayDynamic:
            return f"{self.child_type}[]"
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
            tuples = Type.parse_tuple(s[1:-1])
            tuple_list = []
            for tup in tuples:
                if isinstance(tup, str):
                    tt = Type.type_from_string(str(tup))
                    tuple_list.append(tt)
                elif isinstance(tup, list):
                    tts = list(
                        map(lambda t_: Type.type_from_string(t_), tup)
                    )
                    tuple_list.append(tts)
                else:
                    raise error.ABITypeError(
                        f"cannot convert {tup} to an ABI type"
                    )

            return Type.make_tuple_type(tuple_list)
        else:
            raise error.ABITypeError(f"cannot convert {s} to an ABI type")

    def is_dynamic(self):
        if (
            self.abi_type_id == BaseType.ArrayDynamic
            or self.abi_type_id == BaseType.String
        ):
            return True
        for child in self.child_types:
            if child.is_dynamic():
                return True
        return False

    def parse_tuple(s):
        # If tuple content is empty, return an empty string
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
                if depth == 0:
                    word = word[:-1]
                    if word:
                        tuple_strs.append(word)
                        word = ""
        if word:
            tuple_strs.append(word)
        if depth != 0:
            error.ABITypeError(f"parenthesis mismatch: {s}")
        # print(f"s {s} stack {tuple_strs}")
        return tuple_strs
