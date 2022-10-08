import bisect
from typing import cast, Dict, Any, List, Optional, Iterable, Tuple

from algosdk.error import SourceMapVersionError


"""
TODO: enable sequences of Chunk's to define a Revision 3 Source Map.
e.g cf:
* https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
* OR: https://github.com/algochoi/teal-sourcemap-decoder/blob/main/decode.py

class SourceMap:
    " ""
    More general purpose than TealSourceMap
    " ""
    def __init__(self, source_map: Dict[str, Any]):
        self.version: int = source_map["version"]
        if self.version != 3:
            raise SourceMapVersionError(self.version)

        self.file: Optional[str] = source_map.get("file")
        self.sourceRoot: Optional[str] = source_map.get("sourceRoot")
        self.sources: List[str] = source_map["sources"]
        self.sourcesContent: Optional[List[Optional[str]]] = source_map.get("sourcesContent")
        self.names: List[str] = source_map["names"]
        self.mappings: str = source_map["mappings"]


        pc_list = [
            _decode_int_value(raw_val) for raw_val in self.mappings.split(";")
        ]

        self.pc_to_line: Dict[int, int] = {}
        self.line_to_pc: Dict[int, List[int]] = {}

        last_line = 0
        for index, line_delta in enumerate(pc_list):
            # line_delta is None if the line number has not changed
            # or if the line is empty
            if line_delta is not None:
                last_line = last_line + line_delta

            if last_line not in self.line_to_pc:
                self.line_to_pc[last_line] = []

            self.line_to_pc[last_line].append(index)
            self.pc_to_line[index] = last_line
"""


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

        self.pc_to_line: Dict[int, int] = {}
        self.line_to_pc: Dict[int, List[int]] = {}

        last_line = 0
        for index, line_delta in enumerate(pc_list):
            # line_delta is None if the line number has not changed
            # or if the line is empty
            if line_delta is not None:
                last_line = last_line + line_delta

            if last_line not in self.line_to_pc:
                self.line_to_pc[last_line] = []

            self.line_to_pc[last_line].append(index)
            self.pc_to_line[index] = last_line

    def get_line_for_pc(self, pc: int) -> Optional[int]:
        return self.pc_to_line.get(pc, None)

    def get_pcs_for_line(self, line: int) -> Optional[List[int]]:
        return self.line_to_pc.get(line, None)

    def get_chunks_with_source(self, teal: str) -> List["Chunk"]:
        lines = teal.split("\n")
        assert max(self.pc_to_line.values()) < len(
            lines
        ), f"teal had {len(lines)} lines which can't accommodate the biggest expected line number {max(self.pc_to_line.values())}"

        return [
            Chunk.simple(line, lines[line], pc, f"PC[{pc}]")
            for pc, line in self.pc_to_line.items()
        ]


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


def _base64vlq_decode(vlqval: str) -> List[int]:
    """Decode Base64 VLQ value"""
    results = []
    shift = value = 0
    # use byte values and a table to go from base64 characters to integers
    for v in map(_b64table.__getitem__, vlqval.encode("ascii")):
        v = cast(int, v)
        value += (v & mask) << shift
        if v & flag:
            shift += shiftsize
            continue
        # determine sign and add to results
        results.append((value >> 1) * (-1 if value & 1 else 1))
        shift = value = 0
    return results


from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """Practical data needed for a useful source map"""

    source_line_number: int
    source_line: str
    source_col_bounds: Tuple[int, int]
    target_line_number: int
    target_line: str
    target_col_bounds: Tuple[int, int]

    def __repr__(self) -> str:
        """TODO: this is just a temporary hack"""
        sbnds, tbnds = self.source_col_bounds, self.target_col_bounds
        return (
            "\n"
            + (
                f"source({self.source_line_number}:{sbnds}) --> "
                f"target({self.target_line_number}:{tbnds})"
            )
            + "\n\t\t"
            + f"SANITY CHECK: <<{self.source_line[sbnds[0]:sbnds[1]]}>> =?= <<{self.target_line[tbnds[0]:tbnds[1]]}>>"
        )

    @classmethod
    def simple(
        cls,
        source_line_number: int,
        source_line: str,
        target_line_number: int,
        target_line: str,
    ) -> "Chunk":
        """A simple Chunk consists of an entire line, therefore, the column info is omittef"""
        return cls(
            source_line_number,
            source_line,
            (0, len(source_line)),
            target_line_number,
            target_line,
            (0, len(target_line)),
        )


class FunctionalSourceMapper:
    """
    Callable object mapping target back to original source
    """

    def __init__(self, chunks: Iterable[Chunk]):
        self.chunks = list(chunks)
        self.index = [
            (line, chunk.source_col_bounds[1])
            for line, chunk in enumerate(self.chunks)
        ]

        # TODO: these assertions probly don't belong here

        assert len(self.chunks) == len(self.index)
        assert all(
            idx < self.index[i + 1] for i, idx in enumerate(self.index[:-1])
        )
        assert all(
            self(idx[0], idx[1] - 1) == self.chunks[i]
            for i, idx in enumerate(self.index)
        )

    def __repr__(self) -> str:
        return repr(self.chunks)

    def __call__(self, line: int, column: int) -> Optional[Chunk]:
        idx = bisect.bisect_right(self.index, (line, column))
        if 0 <= idx < len(self.index):
            return self.chunks[idx]
        return None

    def __mul__(
        self, other: "FunctionalSourceMapper"
    ) -> "FunctionalSourceMapper":
        """
        Suppose we've compiled A -> B and also B -> C and that we have
        source maps acting from target to source as follows:
        - self:         C -> B
        - other:        B -> A
        then:
        self * other:   C -> A

        I.e. self * other represents the source map for the composite compilation A -> B -> C
        """
        assert isinstance(other, FunctionalSourceMapper)

        chunks = []
        for schunk in self.chunks:
            ochunk = other(
                schunk.source_line_number, schunk.source_col_bounds[0]
            )
            assert ochunk

            chunks.append(
                Chunk(
                    ochunk.source_line_number,
                    ochunk.source_line,
                    ochunk.source_col_bounds,
                    schunk.target_line_number,
                    schunk.target_line,
                    schunk.source_col_bounds,
                )
            )

        return FunctionalSourceMapper(chunks)

    def target(self) -> str:
        return self.generate_target(self.chunks)

    # TODO: clean up the API - probly don't need the following:

    @classmethod
    def generate_target(cls, chunks: Iterable[Chunk]) -> str:
        return "\n".join(map(lambda chunk: chunk.target_line, chunks))

    @staticmethod
    def construct(
        chunks: Iterable[Chunk],
    ) -> Tuple[str, "FunctionalSourceMapper"]:
        return FunctionalSourceMapper.generate_target(
            chunks
        ), FunctionalSourceMapper(chunks)
