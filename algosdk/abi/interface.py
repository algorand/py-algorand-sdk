import json

from algosdk.abi.method import Method


class Interface:
    """
    Represents a ABI interface description.
    """

    def __init__(self, name, methods) -> None:
        self.name = name
        self.methods = methods

    @staticmethod
    def from_json(resp):
        d = json.loads(resp)
        name = d["name"]
        # TODO: Should we check that method name does not begin with an underscore here?
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Interface(name=name, methods=method_list)
