import json
from typing import List, Union

from algosdk.abi.method import Method


class Contract:
    """
    Represents a ABI contract description.

    Args:
        name (string): name of the contract
        app_id (int): application id associated with the contract
        methods (list): list of Method objects
    """

    def __init__(self, name: str, app_id: int, methods: List[Method]) -> None:
        self.name = name
        self.app_id = int(app_id)
        self.methods = methods

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Contract):
            return False
        return (
            self.name == o.name
            and self.app_id == o.app_id
            and self.methods == o.methods
        )

    @staticmethod
    def from_json(resp: Union[str, bytes, bytearray]) -> "Contract":
        d = json.loads(resp)
        return Contract.undictify(d)

    def dictify(self) -> dict:
        d = {}
        d["name"] = self.name
        d["appId"] = self.app_id
        d["methods"] = [m.dictify() for m in self.methods]
        return d

    @staticmethod
    def undictify(d: dict) -> "Contract":
        name = d["name"]
        app_id = d["appId"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Contract(name=name, app_id=app_id, methods=method_list)
