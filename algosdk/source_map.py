from typing import Dict, Any, List, Tuple

from algosdk.error import SourceMapVersionError


class SourceMap:
    """
    Decodes a VLQ-encoded source mapping between PC values and TEAL source code lines.
    Spec available here: https://sourcemaps.info/spec.html

    Args:
        source_map (dict(str, Any)): source map JSON from algod
    """

    def __init__(self, source_map: Dict[str, Any]):

        self.version: int = source_map["version"]

        if self.version != 3:
            raise SourceMapVersionError(self.version)

        self.sources: List[str] = source_map["sources"]

        self.mappings: str = source_map["mappings"]

        pc_list = [
            _decode_int_value(raw_val) for raw_val in self.mappings.split(";")
        ]

        # Initialize with 0,0 for pc/line
        self.pc_to_line: Dict[int, int] = {}
        self.line_to_pc: Dict[int, List[int]] = {}

        last_line = 0
        for index, line_delta in enumerate(pc_list):
            if line_delta is not None:  # be careful for '0' checks!
                line_num = last_line + line_delta
                if line_num not in self.line_to_pc:
                    self.line_to_pc[line_num] = []
                self.line_to_pc[line_num].append(index)
                last_line = line_num

            self.pc_to_line[index] = last_line

    def get_line_for_pc(self, pc: int) -> int:
        return self.pc_to_line.get(pc, None)

    def get_pcs_for_line(self, line: int) -> List[int]:
        return self.line_to_pc.get(line, None)


def _decode_int_value(value: str) -> int:
    # Mappings may have up to 5 segments:
    # Third segment represents the zero-based starting line in the original source represented.
    decoded_value = _base64vlq_decode(value)
    return decoded_value[2] if decoded_value else None


"""
Source taken from: https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
"""

_b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_b64table = [None] * (max(_b64chars) + 1)
for i, b in enumerate(_b64chars):
    _b64table[b] = i

shiftsize, flag, mask = 5, 1 << 5, (1 << 5) - 1


def _base64vlq_decode(vlqval: str) -> Tuple[int]:
    """Decode Base64 VLQ value"""
    results = []
    shift = value = 0
    # use byte values and a table to go from base64 characters to integers
    for v in map(_b64table.__getitem__, vlqval.encode("ascii")):
        value += (v & mask) << shift
        if v & flag:
            shift += shiftsize
            continue
        # determine sign and add to results
        results.append((value >> 1) * (-1 if value & 1 else 1))
        shift = value = 0
    return results


def _base64vlq_encode(*values: int) -> str:
    """Encode integers to a VLQ value"""
    results = []
    for v in values:
        # add sign bit
        v = (abs(v) << 1) | int(v < 0)
        while True:
            toencode, v = v & mask, v >> shiftsize
            results.append(toencode | (v and flag))
            if not v:
                break
    return bytes(map(_b64chars.__getitem__, results)).decode()
