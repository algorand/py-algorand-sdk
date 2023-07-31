from typing import Dict, Any, Optional


class AVMValue:
    type: int
    uint: int
    bytes: bytes

    def __init__(
        self, *, type: int = 0, uint: int = 0, _bytes: Optional[bytes] = None
    ) -> None:
        self.type = type
        self.uint = uint
        self.bytes = _bytes if _bytes else b""

    def dictify(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "uint": self.uint,
            "bytes": self.bytes,
        }
