import json

from algosdk.abi.method import Method


class Contract:
    """
    Represents a ABI contract description.

    Args:
        name (string): name of the contract
        app_id (int): application id associated with the contract
        methods (list): list of Method objects
    """

    def __init__(self, name, app_id, methods) -> None:
        self.name = name
        self.app_id = app_id
        self.methods = methods

    @staticmethod
    def from_json(resp):
        d = json.loads(resp)
        return Contract.undictify(d)

    def dictify(self):
        d = {}
        d["name"] = self.name
        d["app_id"] = self.app_id
        d["methods"] = [m.dictify() for m in self.methods]
        return d

    @staticmethod
    def undictify(d):
        name = d["name"]
        app_id = d["app_id"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Contract(name=name, app_id=app_id, methods=method_list)
