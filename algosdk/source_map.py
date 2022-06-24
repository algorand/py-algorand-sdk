from typing import Dict, Any, List, Tuple


class SourceMap:
    def __init__(self, map: Dict[str, Any], delimiter: str = ";"):
        self.delimter = delimiter

        self.version: int = map["version"]
        self.sources: List[str] = map["sources"]
        self.mapping: str = map["mapping"]

        pc_list = [
            _decode_int_value(raw_val)
            for raw_val in self.mapping.split(delimiter)
        ]

        # Initialize with 0,0 for pc/line
        self.pc_to_line: Dict[int, int] = {0:0}
        self.line_to_pc: Dict[int, List[int]] = {0:[0]}

        last_line = 0
        for index, line_num in enumerate(pc_list):
            if line_num is not None:  # be careful for '0' checks!
                if line_num not in self.line_to_pc:
                    self.line_to_pc[line_num] = []
                self.line_to_pc[line_num].append(index)
                last_line = line_num

            self.pc_to_line[index] = last_line

    def get_line_for_pc(self, pc: int) -> int:
        return self.pc_to_line[pc]

    def get_pcs_for_line(self, line: int) -> List[int]:
        return self.line_to_pc[line]


def _decode_int_value(value: str) -> int:
    decoded_value = base64vlq_decode(value)
    return decoded_value[2] if decoded_value else None


"""
Source taken from: https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
"""

_b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_b64table = [None] * (max(_b64chars) + 1)
for i, b in enumerate(_b64chars):
    _b64table[b] = i

_shiftsize, _flag, _mask = 5, 1 << 5, (1 << 5) - 1


def base64vlq_decode(vlqval: str) -> Tuple[int]:
    """Decode Base64 VLQ value"""
    results = []
    add = results.append
    shiftsize, flag, mask = _shiftsize, _flag, _mask
    shift = value = 0
    # use byte values and a table to go from base64 characters to integers
    for v in map(_b64table.__getitem__, vlqval.encode("ascii")):
        value += (v & mask) << shift
        if v & flag:
            shift += shiftsize
            continue
        # determine sign and add to results
        add((value >> 1) * (-1 if value & 1 else 1))
        shift = value = 0
    return results


def base64vlq_encode(*values: int) -> str:
    """Encode integers to a VLQ value"""
    results = []
    add = results.append
    shiftsize, flag, mask = _shiftsize, _flag, _mask
    for v in values:
        # add sign bit
        v = (abs(v) << 1) | int(v < 0)
        while True:
            toencode, v = v & mask, v >> shiftsize
            add(toencode | (v and flag))
            if not v:
                break
    return bytes(map(_b64chars.__getitem__, results)).decode()
