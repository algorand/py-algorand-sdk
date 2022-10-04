import json
from typing import List

from algosdk.source_map import Chunk, FunctionalSourceMapper, TealSourceMap


###### FIXTURES ######

quine_preteal = """#pragma version 5
// To modify the program:
// 1. Replace the first line with `pushbytes ""; (test)
// 2. Compile the program.
// 3. Replace the first line with `pushbytes <compiled bytecode>`
// 4. Update the varuint length of the new bytecode (line 11)
// 5. The quine is complete. Compile again.
pushbytes 0x0580004957000280011a504f0149570300505081007200441243
    dup; extract 0 2
pushbytes 0x1a // the varuint length of 0x0580...
    concat; uncover 1; dup
    extract 3 0 // the range here must be updated if the varuint length is longer than 1 byte
    concat; concat // after this line the whole program is on the stack
pushint 0
    app_params_get AppApprovalProgram; assert
==; return"""

quine_teal = """#pragma version 5
// To modify the program:
// 1. Replace the first line with `pushbytes ""; (test)
// 2. Compile the program.
// 3. Replace the first line with `pushbytes <compiled bytecode>`
// 4. Update the varuint length of the new bytecode (line 11)
// 5. The quine is complete. Compile again.
pushbytes 0x0580004957000280011a504f0149570300505081007200441243
dup
extract 0 2
pushbytes 0x1a // the varuint length of 0x0580...
concat
uncover 1
dup
extract 3 0 // the range here must be updated if the varuint length is longer than 1 byte
concat
concat // after this line the whole program is on the stack
pushint 0
app_params_get AppApprovalProgram
assert
==
return"""

quine_json = '{"version":3,"sources":[],"names":[],"mapping":";AAOA;;;;;;;;;;;;;;;;;;;;;;;;;;;;AACA;AACA;;;AACA;;;AACA;AACA;;AACA;AACA;;;AACA;AACA;AACA;;AACA;;AACA;AACA;AACA","mappings":";AAOA;;;;;;;;;;;;;;;;;;;;;;;;;;;;AACA;AACA;;;AACA;;;AACA;AACA;;AACA;AACA;;;AACA;AACA;AACA;;AACA;;AACA;AACA;AACA"}'


### An artificial compiler, to demonstrate composability and `FunctionalSourceMapper`


def pre_compile(pre_teal: str) -> List[Chunk]:
    def at_comment(line: str, idx: int) -> bool:
        return idx < len(line) - 1 and line[idx] == line[idx + 1] == "/"

    tln = 0
    chunks = []
    for sln, sline in enumerate(pre_teal.split("\n")):
        next_line = False
        tline = sline
        bounds = (-1, -1)

        def collect():
            chunks.append(
                Chunk(sln, sline, bounds, tln, tline, (0, len(tline)))
            )

        # special treatment of row 0:
        if sln == 0:
            assert (
                sline[0] == "#"
            ), f"expected immediate pragma with first char '#' but got {sline[0]}"
            next_line = True

        if not next_line:
            lbound = 0
            for j, c in enumerate(sline):
                if c == ";":
                    bounds = (lbound, j)
                    tline = sline[lbound:j].strip()
                    collect()
                    lbound = j + 1
                    tln += 1
                    continue

                if j == len(sline) - 1:
                    bounds = (lbound, j + 1)
                    tline = sline[lbound : j + 1].strip()
                    collect()
                    lbound = j + 1
                    tln += 1
                    continue

                if at_comment(tline, j):
                    next_line = True
                    break

        if next_line:
            bounds = (0, len(tline))
            tline = tline.strip()
            collect()
            tln += 1
            continue

    return chunks


####### UNIT TESTS #######


def test_chunk():
    snum, source = 42, "the source"
    tnum, target = 1337, "the target"

    def bounds(s):
        return (0, len(s))

    assert Chunk(
        snum, source, bounds(source), tnum, target, bounds(target)
    ) == Chunk.simple(snum, source, tnum, target)


def source_mapper_invariants(qsm):
    assert len(qsm.chunks) == len(qsm.index)
    assert all(idx < qsm.index[i + 1] for i, idx in enumerate(qsm.index[:-1]))
    assert all(
        qsm(idx[0], idx[1] - 1) == qsm.chunks[i]
        for i, idx in enumerate(qsm.index)
    )


def construct_sourcemap():
    quine_chunks = pre_compile(quine_preteal)
    for chunk in quine_chunks:
        print(chunk.target_line)

    quine_precompiled, qsm = FunctionalSourceMapper.construct(quine_chunks)

    assert quine_teal == quine_precompiled

    assert quine_chunks == qsm.chunks

    source_mapper_invariants(qsm)
    return qsm


def test_compose_sourcemap():
    quine_d = json.loads(quine_json)
    tsm = TealSourceMap(quine_d)
    teal_source_mapper = FunctionalSourceMapper(
        Chunk.simple(line, f"quine line {line}", pc, f"PC[{pc}]")
        for pc, line in tsm.pc_to_line.items()
    )
    source_mapper_invariants(teal_source_mapper)

    quine_source_mapper = construct_sourcemap()
    product_source_mapper = teal_source_mapper * quine_source_mapper
    source_mapper_invariants(product_source_mapper)

    assert teal_source_mapper.target() == product_source_mapper.target()
    assert len(teal_source_mapper.chunks) == len(product_source_mapper.chunks)
