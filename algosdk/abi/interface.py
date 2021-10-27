import json

from .method import Method
from .. import error


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
        method_list = [Method.undictify(method) for method in d["methods"]]
        return Interface(name=name, methods=method_list)
