from collections import OrderedDict
from typing import List, Tuple

from algosdk import error


class BoxReference:
    def __init__(self, app_index: int, name: str):
        self.app_index = app_index
        self.name = name

    @staticmethod
    def translate_box_references(
        references: List[Tuple[int, str]],
        foreign_apps: List[int],
        this_app_id: int,
    ) -> List["BoxReference"]:
        if not references:
            return []

        box_references = []
        for ref in references:
            # Try coercing reference id and name.
            ref_id, ref_name = int(ref[0]), str(ref[1])
            index = 0
            try:
                # Foreign apps start from index 1; index 0 is its own app ID.
                index = foreign_apps.index(ref_id) + 1
            except ValueError:
                # Check if the app referenced is itself after checking the
                # foreign apps array (in case its own app id is in its own
                # foreign apps array).
                if ref_id == 0 or ref_id == this_app_id:
                    pass
                else:
                    raise error.InvalidForeignAppIdError(
                        f"Box ref with appId {ref_id} not in foreign-apps"
                    )
            box_references.append(BoxReference(index, ref_name))
        return box_references

    def dictify(self):
        d = dict()
        if self.app_index:
            d["i"] = self.app_index
        if self.name:
            d["n"] = self.name
        od = OrderedDict(sorted(d.items()))
        return od

    @staticmethod
    def undictify(d):
        args = {
            "app_index": d["i"] if "i" in d else None,
            "name": d["n"] if "n" in d else None,
        }
        return args

    def __eq__(self, other):
        if not isinstance(other, BoxReference):
            return False
        return self.app_index == other.app_index and self.name == other.name
