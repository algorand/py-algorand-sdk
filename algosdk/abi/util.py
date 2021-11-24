import re

from algosdk.abi.base_type import ABIType
from algosdk.abi.uint_type import UintType
from algosdk.abi.ufixed_type import UfixedType
from algosdk.abi.byte_type import ByteType
from algosdk.abi.bool_type import BoolType
from algosdk.abi.address_type import AddressType
from algosdk.abi.string_type import StringType
from algosdk.abi.array_dynamic_type import ArrayDynamicType
from algosdk.abi.array_static_type import ArrayStaticType
from algosdk.abi.tuple_type import TupleType
from algosdk import error


# Globals
UFIXED_REGEX = r"^ufixed([1-9][\d]*)x([1-9][\d]*)$"
STATIC_ARRAY_REGEX = r"^([a-z\d\[\](),]+)\[([1-9][\d]*)]$"


def type_from_string(s: str) -> ABIType:
    """
    Convert a valid ABI string to a corresponding ABI type.
    """
    if s.endswith("[]"):
        array_arg_type = type_from_string(s[:-2])
        return ArrayDynamicType(array_arg_type)
    elif s.endswith("]"):
        matches = re.search(STATIC_ARRAY_REGEX, s)
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
        matches = re.search(UFIXED_REGEX, s)
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
