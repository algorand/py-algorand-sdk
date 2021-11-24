import json

from algosdk.abi.method import Method


class Interface:
    """
    Represents a ABI interface description.

    Args:
        name (string): name of the interface
        methods (list): list of Method objects
    """

    def __init__(self, name, methods):
        self.name = name
        self.methods = methods

    def __eq__(self, o):
        if not isinstance(o, Interface):
            return False
        return self.name == o.name and self.methods == o.methods

    @staticmethod
    def from_json(resp):
        d = json.loads(resp)
        return Interface.undictify(d)

    def dictify(self):
        d = {}
        d["name"] = self.name
        d["methods"] = [m.dictify() for m in self.methods]
        return d

    @staticmethod
    def undictify(d):
        name = d["name"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Interface(name=name, methods=method_list)
