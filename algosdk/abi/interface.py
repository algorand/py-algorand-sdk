import json
from typing import List, Union, Optional, TypedDict

from algosdk.abi.method import Method, MethodDict, get_method_by_name


# In Python 3.11+ the following classes should be combined using `NotRequired`
class InterfaceDict_Optional(TypedDict, total=False):
    desc: str


class InterfaceDict(InterfaceDict_Optional):
    name: str
    methods: List[MethodDict]


class Interface:
    """
    Represents a ABI interface description.

    Args:
        name (string): name of the interface
        methods (list): list of Method objects
        desc (string, optional): description of the interface
    """

    def __init__(
        self, name: str, methods: List[Method], desc: Optional[str] = None
    ) -> None:
        self.name = name
        self.methods = methods
        self.desc = desc

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Interface):
            return False
        return (
            self.name == o.name
            and self.methods == o.methods
            and self.desc == o.desc
        )

    @staticmethod
    def from_json(resp: Union[str, bytes, bytearray]) -> "Interface":
        d = json.loads(resp)
        return Interface.undictify(d)

    def dictify(self) -> InterfaceDict:
        d: InterfaceDict = {
            "name": self.name,
            "methods": [m.dictify() for m in self.methods],
        }
        if self.desc:
            d["desc"] = self.desc
        return d

    @staticmethod
    def undictify(d: dict) -> "Interface":
        name = d["name"]
        method_list = [Method.undictify(method) for method in d["methods"]]
        desc = d["desc"] if "desc" in d else None
        return Interface(name=name, desc=desc, methods=method_list)

    def get_method_by_name(self, name: str) -> Method:
        return get_method_by_name(self.methods, name)
