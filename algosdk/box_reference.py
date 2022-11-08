from collections import OrderedDict
from typing import List, Tuple, Union

from algosdk import encoding, error


class BoxReference:
    """
    Represents a box reference with a foreign app index and the box name.

    Args:
        app_index (int): index of the application in the foreign app array
        name (bytes): key for the box in bytes
    """

    def __init__(self, app_index: int, name: bytes):
        if app_index < 0:
            raise ValueError(
                f"Box app index must be a non-negative integer: {app_index}"
            )
        self.app_index = app_index
        self.name = name

    @staticmethod
    def translate_box_reference(
        ref: Union[
            Tuple[int, Union[bytes, bytearray, str, int]], "BoxReference"
        ],
        foreign_apps: List[int],
        this_app_id: int,
    ) -> "BoxReference":
        # Do not need to translate the references if they are already BoxReference type.
        if isinstance(ref, BoxReference):
            return ref

        # Try checking reference id and name type.
        ref_id, ref_name = ref[0], encoding.encode_as_bytes(ref[1])
        if not isinstance(ref_id, int):
            raise TypeError("Box reference ID must be an int")

        index = 0
        try:
            # Foreign apps start from index 1; index 0 is its own app ID.
            index = foreign_apps.index(ref_id) + 1
        except (ValueError, AttributeError):
            # Check if the app referenced is itself after checking the
            # foreign apps array (in case its own app id is in its own
            # foreign apps array).
            if ref_id != 0 and ref_id != this_app_id:
                raise error.InvalidForeignIndexError(
                    f"Box ref with appId {ref_id} not in foreign-apps"
                )
        return BoxReference(index, ref_name)

    @staticmethod
    def translate_box_references(
        references: List[Tuple[int, Union[bytes, bytearray, str, int]]],
        foreign_apps: List[int],
        this_app_id: int,
    ) -> List["BoxReference"]:
        """
        Translates a list of tuples with app IDs and names into an array of
        BoxReferences with foreign indices.

        Args:
            references (list[(int, bytes)]): list of tuples specifying app id
                and key for boxes the app may access
            foreign_apps (list[int]): list of other applications in appl call
            this_app_id (int): app ID of the box being references
        """
        if not references:
            return []

        return [
            BoxReference.translate_box_reference(
                ref, foreign_apps, this_app_id
            )
            for ref in references
        ]

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
        return BoxReference(
            d["i"] if "i" in d else 0,
            d["n"] if "n" in d else b"",
        )

    def __eq__(self, other):
        if not isinstance(other, BoxReference):
            return False
        return self.app_index == other.app_index and self.name == other.name
