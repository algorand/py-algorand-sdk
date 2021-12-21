import json
from typing import Dict, List, Union

from algosdk.abi.method import Method


class Contract:
    """
    Represents a ABI contract description.

    Args:
        name (string): name of the contract
        methods (list): list of Method objects
        desc (string, optional): description of the contract
        networks (dict, optional): information about the contract in a particular network,
            such as app-id.
    """

    def __init__(
        self,
        name: str,
        methods: List[Method],
        desc: str = None,
        networks: Dict[str, dict] = None,
    ) -> None:
        self.name = name
        self.methods = methods
        self.desc = desc
        self.networks = networks

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Contract):
            return False
        return (
            self.name == o.name
            and self.methods == o.methods
            and self.desc == o.desc
            and self.networks == o.networks
        )

    @staticmethod
    def from_json(resp: Union[str, bytes, bytearray]) -> "Contract":
        d = json.loads(resp)
        return Contract.undictify(d)

    def dictify(self) -> dict:
        d = {}
        d["name"] = self.name
        d["desc"] = self.desc
        d["networks"] = self.networks
        d["methods"] = [m.dictify() for m in self.methods]
        return d

    @staticmethod
    def undictify(d: dict) -> "Contract":
        name = d["name"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        desc = d["desc"] if "desc" in d else None
        networks = d["networks"] if "networks" in d else None
        return Contract(
            name=name, desc=desc, networks=networks, methods=method_list
        )
