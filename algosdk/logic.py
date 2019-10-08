import json
import os

from . import error

spec = None
opcodes = None

MAX_COST = 20000
MAX_LENGTH = 1000

def check_program(program, args=None):
    """
    Performs program checking for max length and cost

    Args:
        program (bytes)
        args (list[bytes])

    Returns:
        True on success
        Raises InvalidProgram on error
    """

    global spec, opcodes

    if not program:
        raise error.InvalidProgram("empty program")
    if not args:
        args = []

    if spec is None:
        script_path = os.path.realpath(__file__)
        script_dir = os.path.dirname(script_path)
        langspec_file = os.path.join(script_dir, "data", "langspec.json")
        with open(langspec_file, "rt") as fin:
            spec = json.load(fin)

    version, vlen = parse_uvariant(program)
    if vlen <= 0 or version > spec["EvalMaxVersion"]:
        raise error.InvalidProgram("unsupported version")

    cost = 0
    length = len(program)
    for arg in args:
        length += len(arg)

    if length >= MAX_LENGTH:
        raise error.InvalidProgram("program too long")

    if opcodes is None:
        opcodes = dict()
        for op in spec['Ops']:
            opcodes[op['Opcode']] = op

    pc = vlen
    while pc < len(program):
        op = opcodes.get(program[pc], None)
        if op is None:
            raise error.InvalidProgram("invalid instruction")

        cost += op['Cost']
        size = op['Size']
        if size == 0:
            if op['Opcode'] == 32:  # intcblock
                size += check_int_const_block(program, pc)
            elif op['Opcode'] == 38:    # bytecblock
                size += check_byte_const_block(program, pc)
            else:
                raise error.InvalidProgram("invalid instruction")
        pc += size

    if cost >= MAX_COST:
        raise error.InvalidProgram("program too costly to run")

    return True

def check_int_const_block(program, pc):
    size = 1
    num_ints, bytes_used = parse_uvariant(program[pc + size:])
    if bytes_used <= 0:
        raise error.InvalidProgram("could not decode int const block size at pc=%d" % (pc + size))
    size += bytes_used
    for i in range(0, num_ints):
        if pc + size >= len(program):
            raise error.InvalidProgram("intcblock ran past end of program")
        _, bytes_used = parse_uvariant(program[pc + size:])
        if bytes_used <= 0:
            raise error.InvalidProgram("could not decode int const[%d] at pc=%d" % (i, pc + size))
        size += bytes_used
    return size

def check_byte_const_block(program, pc):
    size = 1
    num_ints, bytes_used = parse_uvariant(program[pc + size:])
    if bytes_used <= 0:
        raise error.InvalidProgram("could not decode []byte const block size at pc=%d" % (pc + size))
    size += bytes_used
    for i in range(0, num_ints):
        if pc + size >= len(program):
            raise error.InvalidProgram("bytecblock ran past end of program")
        item_len, bytes_used = parse_uvariant(program[pc + size:])
        if bytes_used <= 0:
            raise error.InvalidProgram("could not decode []byte const[%d] at pc=%d" % (i, pc + size))
        size += bytes_used
        if pc + size >= len(program):
            raise error.InvalidProgram("bytecblock ran past end of program")
        size += item_len
    return size

def parse_uvariant(buf):
    x = 0
    s = 0
    for i, b in enumerate(buf):
        if b < 0x80:
            if i > 9 or i == 9 and b > 1:
                return 0, -(i + 1)
            return x | int(b) <<s, i + 1
        x |= int(b & 0x7f) << s
        s += 7

    return 0, 0