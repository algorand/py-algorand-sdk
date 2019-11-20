import json
import os

from . import constants
from . import error
from . import encoding

spec = None
opcodes = None


def check_program(program, args=None):
    """
    Performs program checking for max length and cost

    Args:
        program (bytes): compiled program
        args (list[bytes]): args are not signed, but are checked by logic

    Returns:
        bool: True on success

    Raises:
        InvalidProgram: on error
    """

    global spec, opcodes
    intcblock_opcode = 32
    bytecblock_opcode = 38

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

    version, vlen = parse_uvarint(program)
    if vlen <= 0 or version > spec["EvalMaxVersion"]:
        raise error.InvalidProgram("unsupported version")

    cost = 0
    length = len(program)
    for arg in args:
        length += len(arg)

    if length > constants.logic_sig_max_size:
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
            if op['Opcode'] == intcblock_opcode:
                size += check_int_const_block(program, pc)
            elif op['Opcode'] == bytecblock_opcode:
                size += check_byte_const_block(program, pc)
            else:
                raise error.InvalidProgram("invalid instruction")
        pc += size

    if cost >= constants.logic_sig_max_cost:
        raise error.InvalidProgram("program too costly to run")

    return True


def check_int_const_block(program, pc):
    size = 1
    num_ints, bytes_used = parse_uvarint(program[pc + size:])
    if bytes_used <= 0:
        raise error.InvalidProgram("could not decode int const block size at pc=%d" % (pc + size))
    size += bytes_used
    for i in range(0, num_ints):
        if pc + size >= len(program):
            raise error.InvalidProgram("intcblock ran past end of program")
        _, bytes_used = parse_uvarint(program[pc + size:])
        if bytes_used <= 0:
            raise error.InvalidProgram("could not decode int const[%d] at pc=%d" % (i, pc + size))
        size += bytes_used
    return size


def check_byte_const_block(program, pc):
    size = 1
    num_ints, bytes_used = parse_uvarint(program[pc + size:])
    if bytes_used <= 0:
        raise error.InvalidProgram("could not decode []byte const block size at pc=%d" % (pc + size))
    size += bytes_used
    for i in range(0, num_ints):
        if pc + size >= len(program):
            raise error.InvalidProgram("bytecblock ran past end of program")
        item_len, bytes_used = parse_uvarint(program[pc + size:])
        if bytes_used <= 0:
            raise error.InvalidProgram("could not decode []byte const[%d] at pc=%d" % (i, pc + size))
        size += bytes_used
        if pc + size >= len(program):
            raise error.InvalidProgram("bytecblock ran past end of program")
        size += item_len
    return size


def parse_uvarint(buf):
    x = 0
    s = 0
    for i, b in enumerate(buf):
        if b < 0x80:
            if i > 9 or i == 9 and b > 1:
                return 0, -(i + 1)
            return x | int(b) << s, i + 1
        x |= int(b & 0x7f) << s
        s += 7

    return 0, 0


def address(program):
    """
    Return the address of the program.

    Args:
        program (bytes): compiled program

    Returns:
        str: program address
    """
    to_sign = constants.logic_prefix + program
    checksum = encoding.checksum(to_sign)
    return encoding.encode_address(checksum)
