import json

from algosdk.abi.method import Method


class Contract:
    """
    Represents a ABI contract description.
    """

    def __init__(self, name, app_id, methods) -> None:
        self.name = name
        self.app_id = app_id
        self.methods = methods

    @staticmethod
    def from_json(resp):
        d = json.loads(resp)
        name = d["name"]
        app_id = d["app_id"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Contract(name=name, app_id=app_id, methods=method_list)
