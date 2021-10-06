import re

from .uint_type import UintType
from .ufixed_type import UfixedType
from .byte_type import ByteType
from .bool_type import BoolType
from .address_type import AddressType
from .string_type import StringType
from .array_dynamic_type import ArrayDynamicType
from .array_static_type import ArrayStaticType
from .tuple_type import TupleType
from .. import error


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
    if s.startswith("uint"):
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
