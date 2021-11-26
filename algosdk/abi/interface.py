import json
from typing import List, Union

from algosdk.abi.method import Method


class Interface:
    """
    Represents a ABI interface description.

    Args:
        name (string): name of the interface
        methods (list): list of Method objects
    """

    def __init__(self, name: str, methods: List[Method]) -> None:
        self.name = name
        self.methods = methods

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Interface):
            return False
        return self.name == o.name and self.methods == o.methods

    @staticmethod
    def from_json(resp: Union[str, bytes, bytearray]) -> "Interface":
        d = json.loads(resp)
        return Interface.undictify(d)

    def dictify(self) -> dict:
        d = {}
        d["name"] = self.name
        d["methods"] = [m.dictify() for m in self.methods]
        return d

    @staticmethod
    def undictify(d: dict) -> "Interface":
        name = d["name"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Interface(name=name, methods=method_list)
