from collections import OrderedDict
from os import access
from typing import List, Optional, Tuple, Union

from algosdk import encoding
from algosdk.box_reference import BoxReference


def translate_to_resource_references(
    app_id: int,
    accounts: Optional[List[str]] = None,
    foreign_assets: Optional[List[int]] = None,
    foreign_apps: Optional[List[int]] = None,
    boxes: Optional[List[Tuple[int, bytes]]] = None,
    holdings: Optional[List[Tuple[int, str]]] = None,
    locals: Optional[List[Tuple[int, str]]] = None,
) -> List["ResourceReference"]:
    """
    Convert accounts, apps, assets, boxes, holdings, locals into list of ResourceReference
    that is suitable for txn.Access field creation.

    Args:
        app_id (int): current application id
        accounts (list[string], optional): list of additional accounts involved in call
        foreign_apps (list[int], optional): list of other applications (identified by index) involved in call
        foreign_assets (list[int], optional): list of assets involved in call
        boxes(list[(int, bytes)], optional): list of tuples specifying app id and key for boxes the app may access
        holdings (list[int, str], optional): lists of tuples specifying the asset holdings to be accessed during evaluation of the application;
            zero (empty) address means sender
        locals (list[int, str], optional): lists of tuples specifying the local states to be accessed during evaluation of the application;
            zero (empty) address means sender
    """
    access: List["ResourceReference"] = []

    def ensure(target: "ResourceReference") -> int:
        for idx, a in enumerate(access):
            if (
                a.address == target.address
                and a.asset_id == target.asset_id
                and a.app_id == target.app_id
            ):
                return idx + 1
        access.append(target)
        return len(access)

    for account in accounts or []:
        ensure(ResourceReference(address=account))

    for asset in foreign_assets or []:
        ensure(ResourceReference(asset_id=asset))

    for app in foreign_apps or []:
        ensure(ResourceReference(app_id=app))

    for asset, addr in holdings or []:
        addr_idx = 0
        if addr:
            addr_idx = ensure(ResourceReference(address=addr))
        asset_idx = ensure(ResourceReference(asset_id=asset))
        access.append(
            ResourceReference(
                holding_reference=HoldingRef(
                    asset_index=asset_idx, addr_index=addr_idx
                )
            )
        )

    for app, addr in locals or []:
        app_idx = 0
        if app and app != app_id:
            app_idx = ensure(ResourceReference(app_id=app))
        addr_idx = 0
        if addr:
            addr_idx = ensure(ResourceReference(address=addr))
        access.append(
            ResourceReference(
                locals_reference=LocalsRef(
                    app_index=app_idx, addr_index=addr_idx
                )
            )
        )

    for app, name in boxes or []:
        app_idx = 0
        if app and app != app_id:
            app_idx = ensure(ResourceReference(app_id=app))
        access.append(
            ResourceReference(
                box_reference=BoxReference(app_index=app_idx, name=name)
            )
        )

    return access


class ResourceReference:
    def __init__(
        self,
        address: Optional[str] = None,
        asset_id: Optional[int] = None,
        app_id: Optional[int] = None,
        box_reference: Optional[BoxReference] = None,
        holding_reference: Optional["HoldingRef"] = None,
        locals_reference: Optional["LocalsRef"] = None,
    ):
        self.app_id = app_id
        self.address = address
        self.asset_id = asset_id
        self.box_reference = box_reference
        self.holding_reference = holding_reference
        self.locals_reference = locals_reference

    def dictify(self):
        d = dict()
        if self.address:
            d["d"] = encoding.decode_address(self.address)
        if self.asset_id:
            d["s"] = self.asset_id
        if self.app_id:
            d["p"] = self.app_id
        if self.box_reference:
            d["b"] = self.box_reference.dictify()
        if self.holding_reference:
            d["h"] = self.holding_reference.dictify()
        if self.locals_reference:
            d["l"] = self.locals_reference.dictify()
        od = OrderedDict(sorted(d.items()))
        return od

    @staticmethod
    def undictify(d):
        return ResourceReference(
            address=encoding.encode_address(d["d"]) if "d" in d else "",
            asset_id=d["s"] if "s" in d else None,
            app_id=d["p"] if "p" in d else None,
            box_reference=BoxReference.undictify(d["b"]) if "b" in d else None,
            holding_reference=(
                HoldingRef.undictify(d["h"]) if "h" in d else None
            ),
            locals_reference=LocalsRef.undictify(d["l"]) if "l" in d else None,
        )

    def __eq__(self, value):
        if not isinstance(value, ResourceReference):
            return False
        return (
            self.address == value.address
            and self.asset_id == value.asset_id
            and self.app_id == value.app_id
            and self.box_reference == value.box_reference
            and self.holding_reference == value.holding_reference
            and self.locals_reference == value.locals_reference
        )


class LocalsRef:
    """
    Represents a local reference in txn.Access with an app index and address index.

    Args:
        app_index (int): index of the application in the access array
        addr_index (int): index of the address in the access array
    """

    def __init__(self, app_index: int, addr_index: int):
        self.app_index = app_index
        self.addr_index = addr_index

    def dictify(self):
        d = dict()
        if self.app_index:
            d["p"] = self.app_index
        if self.addr_index:
            d["d"] = self.addr_index
        od = OrderedDict(sorted(d.items()))
        return od

    @staticmethod
    def undictify(d):
        return LocalsRef(
            d["p"] if "p" in d else 0,
            d["d"] if "d" in d else 0,
        )

    def __eq__(self, other):
        if not isinstance(other, LocalsRef):
            return False
        return (
            self.app_index == other.app_index
            and self.addr_index == other.addr_index
        )


class HoldingRef:
    """
    Represents a holding reference in txn.Access with an asset index and address index.

    Args:
        asset_index (int): index of the asset in the access array
        addr_index (int): index of the address in the access array
    """

    def __init__(self, asset_index: int, addr_index: int):
        self.asset_index = asset_index
        self.addr_index = addr_index

    def dictify(self):
        d = dict()
        if self.asset_index:
            d["s"] = self.asset_index
        if self.addr_index:
            d["d"] = self.addr_index
        od = OrderedDict(sorted(d.items()))
        return od

    @staticmethod
    def undictify(d):
        return HoldingRef(
            d["s"] if "s" in d else 0,
            d["d"] if "d" in d else 0,
        )

    def __eq__(self, other):
        if not isinstance(other, HoldingRef):
            return False
        return (
            self.asset_index == other.asset_index
            and self.addr_index == other.addr_index
        )
