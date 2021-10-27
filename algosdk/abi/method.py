import json
import re
from .. import error

from Cryptodome.Hash import SHA512


# Globals
PARENTHESES_REGEX = r"\(|\)|,"


class Method:
    """
    Represents a ABI method description.

    Args:
        name (string): name of the method
        args (list): list of Argument objects with type, name, and optional description
        returns (Returns): a Returns object with a type and optional description
        desc (string, optional): optional description of the method
    """

    def __init__(self, name, args, returns, desc=None) -> None:
        self.name = name
        self.args = args
        self.desc = desc
        self.returns = (
            returns if (returns and returns.type != "void") else None
        )

    def get_signature(self):
        arg_string = ",".join([arg.type for arg in self.args])
        ret_string = self.returns.type if self.returns else "void"
        return "{}({}){}".format(self.name, arg_string, ret_string)

    def get_selector(self):
        """
        Returns the ABI method signature, which is the first four bytes of the
        SHA-512/256 hash of the method signature.

        Returns:
            bytes: first four bytes of the method signature hash
        """
        hash = SHA512.new(truncate="256")
        hash.update((self.get_signature()).encode("utf-8"))
        return hash.digest()[:4]

    @staticmethod
    def from_json(resp):
        method_dict = json.loads(resp)
        return Method.undictify(method_dict)

    @staticmethod
    def from_string(s):
        # Split string into tokens around parentheses and commas.
        # The first token should always be the name of the method,
        # and the last token should be the return type (or void).
        tokens = re.split(PARENTHESES_REGEX, s)
        if len(tokens) < 3:
            raise error.ABITypeError(
                "ABI method string is malformed {}".format(s)
            )
        argument_list = [Argument(t) for t in tokens[1:-1]]
        return_type = Returns(tokens[-1])
        return Method(name=tokens[0], args=argument_list, returns=return_type)

    @staticmethod
    def undictify(d):
        name = d["name"]
        arg_list = [Argument.undictify(arg) for arg in d["args"]]
        return_obj = (
            Returns.undictify(d["returns"]) if "returns" in d else None
        )
        desc = d["desc"] if "desc" in d else None
        return Method(name=name, args=arg_list, returns=return_obj, desc=desc)


class Argument:
    """
    Represents an argument for a ABI method

    Args:
        type (string): ABI type of this method argument
        name (string, optional): name of this method argument
        desc (string, optional): description of this method argument
    """

    def __init__(self, type, name=None, desc=None) -> None:
        self.type = type
        self.name = name
        self.desc = desc

    def __str__(self):
        return self.type

    @staticmethod
    def undictify(d):
        return Argument(
            type=d["type"],
            name=d["name"],
            desc=d["desc"] if "desc" in d else None,
        )


class Returns:
    """
    Represents a return type for a ABI method

    Args:
        type (string): ABI type of this return argument
        desc (string, optional): description of this return argument
    """

    def __init__(self, type, desc=None) -> None:
        self.type = type
        self.desc = desc

    def __str__(self):
        return self.type

    @staticmethod
    def undictify(d):
        return Returns(type=d["type"], desc=d["desc"] if "desc" in d else None)
