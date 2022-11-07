import bisect
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from itertools import count

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    TypedDict,
    Union,
    cast,
)

from algosdk.error import SourceMapVersionError


@dataclass(frozen=True)
class SourceMapJSON:
    version: Literal[3]
    sources: List[str]
    names: List[str]
    mappings: str
    file: Optional[str] = None
    sourceRoot: Optional[str] = None
    sourcesContent: Optional[List[Optional[str]]] = None


"""

{
"version" : 3,
"file": "out.js",
"sourceRoot": "",
"sources": ["foo.js", "bar.js"],
"sourcesContent": [null, null],
"names": ["src", "maps", "are", "fun"],
"mappings": "A,AAAB;;ABCDE;"
}

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


def _decode_int_value(value: str) -> Optional[int]:
    # Mappings may have up to 5 segments:
    # Third segment represents the zero-based starting line in the original source represented.
    decoded_value = _base64vlq_decode(value)
    return decoded_value[2] if decoded_value else None


"""
Source taken from: https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
"""

_b64chars = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_b64table = [-1] * (max(_b64chars) + 1)
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


def _base64vlq_encode(*values: int) -> str:
    """Encode integers to a VLQ value"""
    results = []
    add = results.append
    for v in values:
        # add sign bit
        v = (abs(v) << 1) | int(v < 0)
        while True:
            toencode, v = v & mask, v >> shiftsize
            add(toencode | (v and flag))
            if not v:
                break
    # TODO: latest version of gist avoids the decode() step
    return bytes(map(_b64chars.__getitem__, results)).decode()


@dataclass(frozen=True)
class Chunk:
    """THIS IS DEPRECATED
    Practical data needed for a useful source map
    """

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
    TODO: this is probly going away completely
    Callable object mapping target back to original source
    """

    def __init__(
        self,
        indexer: List[Tuple[int, int]],
        chunks: List[Chunk],
        source_map: Optional[SourceMapJSON] = None,
    ):
        self.index = indexer
        self.chunks = chunks
        self.source_map: Optional[SourceMapJSON] = source_map

    @staticmethod
    def from_chunks(chunks: Iterable[Chunk]) -> "FunctionalSourceMapper":
        chunks = list(chunks)
        indexer = [
            (line, chunk.source_col_bounds[1])
            for line, chunk in enumerate(chunks)
        ]

        # TODO: these assertions probly don't belong here

        assert len(chunks) == len(indexer)
        assert all(idx < indexer[i + 1] for i, idx in enumerate(indexer[:-1]))

        fsm = FunctionalSourceMapper(indexer, chunks)
        assert all(
            fsm(idx[0], idx[1] - 1) == chunks[i]
            for i, idx in enumerate(indexer)
        )

        return fsm

    @staticmethod
    def from_map(
        m: Mapping[str, Any], source: str, pop_mapping: bool = False
    ) -> SourceMapJSON:
        if pop_mapping:
            m = {**m}
            m.pop("mapping")
        smj = SourceMapJSON(**m)

        return smj

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

        return FunctionalSourceMapper.from_chunks(chunks)

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
        ), FunctionalSourceMapper.from_chunks(chunks)


#### ---- Based on mjpieters CODE ---- ####

"""Extract generated -> source mappings"""


class autoindex(defaultdict):
    def __init__(self, *args, **kwargs):
        super().__init__(partial(next, count()), *args, **kwargs)


@dataclass(frozen=False)
class R3SourceMapping:
    line: int
    # line_end: Optional[int] = None #### NOT PROVIDED (AND NOT CONFORMING WITH R3 SPEC) AS TARGETS ARE ASSUMED TO SPAN AT MOST ONE LINE ####
    column: int
    column_end: Optional[int] = None
    source: Optional[str] = None
    source_line: Optional[int] = None
    source_column: Optional[int] = None
    source_line_end: Optional[int] = None
    source_column_end: Optional[int] = None
    name: Optional[str] = None
    source_extract: Optional[str] = None
    target_extract: Optional[str] = None
    source_content: Optional[List[str]] = None

    def __post_init__(self):
        if self.source is not None and (
            self.source_line is None or self.source_column is None
        ):
            raise TypeError(
                "Invalid source mapping; missing line and column for source file"
            )
        if self.name is not None and self.source is None:
            raise TypeError(
                "Invalid source mapping; name entry without source location info"
            )

    def __lt__(self, other: "R3SourceMapping") -> bool:
        assert isinstance(
            other, type(self)
        ), f"received incomparable {type(other)}"

        return (self.line, self.column) < (other.line, other.column)

    def __ge__(self, other: "R3SourceMapping") -> bool:
        return not self < other

    def location(self, source=False) -> Tuple[str, int, int]:
        return (
            (
                self.source if self.source else "",
                self.source_line if self.source_line else -1,
                self.source_column if self.source_column else -1,
            )
            if source
            else ("", self.line, self.column)
        )

    @property
    def content_line(self) -> Optional[str]:
        try:
            # self.source_content.splitlines()[self.source_line]  # type: ignore
            self.source_content[self.source_line]  # type: ignore
        except (TypeError, IndexError):
            return None

    @classmethod
    def extract_window(
        cls,
        source_lines: Optional[List[str]],
        line: int,
        column: int,
        right_column: Optional[int],
    ) -> Optional[str]:
        return (
            (
                source_lines[line][column:right_column]
                if right_column is not None
                else source_lines[line][column:]
            )
            if source_lines
            else None
        )

    def __str__(self) -> str:
        def swindow(file, line, col, rcol, extract):
            if file == "unknown":
                file = None
            if not rcol:
                rcol = ""
            if extract is None:
                extract = "?"
            return f"{file + '::' if file else ''}L{line}C{col}-{rcol}='{extract}'"

        return (
            f"{swindow(self.source, self.source_line, self.source_column, self.source_column_end, self.source_extract)} <- "
            f"{swindow(None, self.line, self.column, self.column_end, self.target_extract)}"
        )

    __repr__ = __str__


class R3SourceMapJSON(TypedDict, total=False):
    version: Literal[3]
    file: Optional[str]
    sourceRoot: Optional[str]
    sources: List[str]
    sourcesContent: Optional[List[Optional[str]]]
    names: List[str]
    mappings: str


@dataclass(frozen=True)
class R3SourceMap:
    """
    Modified from the original `SourceMap` available under MIT License here (as of Oct. 12, 2022): https://gist.github.com/mjpieters/86b0d152bb51d5f5979346d11005588b
    `R3` is a nod to "Revision 3" of John Lenz's Source Map Proposal: https://docs.google.com/document/d/1U1RGAehQwRypUTovF1KRlpiOFze0b-_2gc6fAH0KY0k/edit?hl=en_US&pli=1&pli=1
    """

    file: Optional[str]
    source_root: Optional[str]
    entries: Mapping[Tuple[int, int], R3SourceMapping]
    index: List[Tuple[int, ...]] = field(default_factory=list)
    file_lines: Optional[List[str]] = None
    source_files: Optional[List[str]] = None
    source_files_lines: Optional[List[List[str]]] = None

    def __post_init__(self):
        entries = list(self.entries.values())
        for i, entry in enumerate(entries):
            if i + 1 >= len(entries):
                return

            if entry >= entries[i + 1]:
                raise TypeError(
                    f"Invalid source map as entries aren't properly ordered: entries[{i}] = {entry} >= entries[{i+1}] = {entries[i + 1]}"
                )

    def __repr__(self) -> str:
        parts = []
        if self.file is not None:
            parts += [f"file={self.file!r}"]
        if self.source_root is not None:
            parts += [f"source_root={self.source_root!r}"]
        parts += [f"len={len(self.entries)}"]
        return f"<MJPSourceMap({', '.join(parts)})>"

    @classmethod
    def from_json(
        cls,
        smap: R3SourceMapJSON,
        sources_override: Optional[List[str]] = None,
        sources_content_override: List[str] = [],
        target: Optional[str] = None,
        add_right_bounds: bool = True,
    ) -> "R3SourceMap":
        """
        NOTE about `*_if_missing` arguments
        * sources_override - STRICTLY SPEAKING `sources` OUGHT NOT BE MISSING OR EMPTY in R3SourceMapJSON.
            However, currently the POST v2/teal/compile endpoint populate this field with an empty list, as it is not provided the name of the
            Teal file which is being compiled. In order comply with the R3 spec, this field is populated with ["unknown"] when either missing or empty
            in the JSON and not supplied during construction.
            An error will be raised when attempting to replace a nonempty R3SourceMapJSON.sources.
        * sources_content_override - `sourcesContent` is optional and this provides a way at runtime to supply the actual source.
            When provided, and the R3SourceMapJSON is either missing or empty, this will be substituted.
            An error will be raised when attempting to replace a nonempty R3SourceMapJSON.sourcesContent.
        """
        # TODO: the following mypy errors goes away with the dataclass
        if smap["version"] != 3:
            raise ValueError("Only version 3 sourcemaps are supported ")
        entries, index = {}, []
        spos = npos = sline = scol = 0

        sources = smap.get("sources")
        if sources and sources_override:
            raise AssertionError(
                "ambiguous sources from JSON and method argument"
            )
        sources = sources or sources_override or ["unknown"]

        contents = smap.get("sourcesContent")
        if contents and sources_content_override:
            raise AssertionError(
                "ambiguous sourcesContent from JSON and method argument"
            )
        contents = contents or sources_content_override

        names = smap.get("names")

        tcont, sp_conts = (
            target.splitlines() if target else None,
            [c.splitlines() for c in contents],
        )

        for gline, vlqs in enumerate(smap["mappings"].split(";")):
            index += [[]]
            if not vlqs:
                continue
            gcol = 0
            for gcd, *ref in map(_base64vlq_decode, vlqs.split(",")):
                gcol += gcd
                kwargs = {}
                if len(ref) >= 3:
                    sd, sld, scd, *namedelta = ref
                    spos, sline, scol = spos + sd, sline + sld, scol + scd
                    scont = sp_conts[spos] if len(sp_conts) > spos else None  # type: ignore
                    # extract the referenced source till the end of the current line
                    extract = R3SourceMapping.extract_window
                    kwargs = {
                        "source": sources[spos]
                        if spos < len(sources)
                        else None,
                        "source_line": sline,
                        "source_column": scol,
                        "source_content": scont,
                        "source_extract": extract(scont, sline, scol, None),
                        "target_extract": extract(tcont, gline, gcol, None),
                    }
                    if namedelta:
                        npos += namedelta[0]
                        kwargs["name"] = names[npos]
                entries[gline, gcol] = R3SourceMapping(
                    line=gline, column=gcol, **kwargs
                )
                index[gline].append(gcol)

        sourcemap = cls(
            smap.get("file"),
            smap.get("sourceRoot"),
            entries,
            [tuple(cs) for cs in index],
            tcont,
            sources,
            sp_conts,
        )
        if add_right_bounds:
            sourcemap.add_right_bounds()
        return sourcemap

    def add_right_bounds(self) -> None:
        entries = list(self.entries.values())
        for i, entry in enumerate(entries):
            if i + 1 >= len(entries):
                continue

            next_entry = entries[i + 1]

            def same_line_less_than(lc, nlc):
                return (lc[0], lc[1]) == (nlc[0], nlc[1]) and lc[2] < nlc[2]

            if not same_line_less_than(
                entry.location(), next_entry.location()
            ):
                continue
            entry.column_end = next_entry.column
            entry.target_extract = entry.extract_window(
                self.file_lines, entry.line, entry.column, entry.column_end
            )

            if not all(
                [
                    self.source_files,
                    self.source_files_lines,
                    next_entry.source,
                    same_line_less_than(
                        entry.location(source=True),
                        next_entry.location(source=True),
                    ),
                ]
            ):
                continue
            entry.source_column_end = next_entry.source_column
            try:
                fidx = self.source_files.index(next_entry.source)  # type: ignore
            except ValueError:
                continue
            entry.source_extract = entry.extract_window(
                self.source_files_lines[fidx],
                entry.source_line,  # type: ignore
                entry.source_column,  # type: ignore
                next_entry.source_column,
            )

    def to_json(self, with_contents: bool = False) -> R3SourceMapJSON:
        content, mappings = [], []
        sources, names = autoindex(), autoindex()
        entries = self.entries
        spos = sline = scol = npos = 0
        for gline, cols in enumerate(self.index):
            gcol = 0
            mapping = []
            for col in cols:
                entry = entries[gline, col]
                ds, gcol = [col - gcol], col

                if entry.source is not None:
                    assert entry.source_line is not None
                    assert entry.source_column is not None
                    ds += (
                        sources[entry.source] - spos,
                        entry.source_line - sline,
                        entry.source_column - scol,
                    )
                    spos, sline, scol = (
                        spos + ds[1],
                        sline + ds[2],
                        scol + ds[3],
                    )
                    if spos == len(content):
                        c = entry.source_content
                        content.append("\n".join(c) if c else None)
                    if entry.name is not None:
                        ds += (names[entry.name] - npos,)
                        npos += ds[-1]
                mapping.append(_base64vlq_encode(*ds))

            mappings.append(",".join(mapping))

        encoded = {
            "version": 3,
            "sources": [
                s for s, _ in sorted(sources.items(), key=lambda si: si[1])
            ],
            "names": [
                n for n, _ in sorted(names.items(), key=lambda ni: ni[1])
            ],
            "mappings": ";".join(mappings),
        }
        if with_contents:
            encoded["sourcesContent"] = content
        if self.file is not None:
            encoded["file"] = self.file
        if self.source_root is not None:
            encoded["sourceRoot"] = self.source_root
        return encoded  # type: ignore

    def __getitem__(self, idx: Union[int, Tuple[int, int]]):
        l: int
        c: int
        try:
            l, c = idx  # type: ignore   # The exception handler deals with the int case
        except TypeError:
            l, c = idx, 0  # type: ignore   # yes, idx is guaranteed to be an int
        try:
            return self.entries[l, c]
        except KeyError:
            # find the closest column
            if not (cols := self.index[l]):
                raise IndexError(idx)
            cidx = bisect.bisect(cols, c)
            return self.entries[l, cols[cidx and cidx - 1]]
