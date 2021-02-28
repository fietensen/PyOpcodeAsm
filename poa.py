"""
Module for compiling Python opcode instructions 
"""

__version__ = '0.1'
__author__ = 'Fiete Minge'

import sys
import os
import types
import _opcode

def parse_definition_file(fp) -> dict[str, tuple[int, bool]]:
    def _canconv(t, v):
        try:
            _=t(v)
            return True

        except Exception:
            return False

    opcode_definitions = {}
    for line in fp.readlines():
        if line.startswith('#define '):
            _s = list(filter(lambda x:x, line.strip().split(' ')))
            if len(_s) == 3 and _canconv(int, _s[-1]):
                opcode_definitions[_s[1]] = int(_s[2])
    
    if (_have_argument := opcode_definitions.get('HAVE_ARGUMENT')):
        opcode_definitions = {name: (opcode, opcode>=_have_argument) for name, opcode in opcode_definitions.items()}
    else:
        return None
    del opcode_definitions['HAVE_ARGUMENT']

    return opcode_definitions    

def parse_opcode_file(fp) -> tuple[list[tuple[str, int]], bytes]:
    def _canconv(t, v):
        try:
            _=t(v)
            return True

        except Exception:
            return False

    exec_flow = []
    lines = []
    idx = 0

    for lidx, line in enumerate(fp.readlines()):
        line = line.strip()

        if line.replace(' ', '').replace('\t', '').startswith('//') or not line:
            continue

        if line.endswith(":") and _canconv(int, line[:-1]):
            linenr = int(line[:-1])
            cur_offset = idx
            lines.append((linenr, cur_offset))
            continue

        params = list(filter(lambda x:x,
            line.strip().replace('\t', ' ').split(' ')))

        if len(params) == 2 and opcodes.get(params[0]) and opcodes[params[0]][1] and _canconv(int, params[1]):
            exec_flow.append((params[0], int(params[1])))
        elif len(params) == 1 and opcodes.get(params[0]) and (not opcodes[params[0]][1]):
            exec_flow.append((params[0], None))
        else:
            print("[ERROR]: Failed parsing in line {}".format(lidx))
            return None
        
        idx += 2

    lnotab = []
    for lidx, line_info in enumerate(lines):
        if lidx == 0:
            # byte increase = 0 since it's the beginning of the bytecode
            lnotab.append(0) 
            lnotab.append(line_info[0]) # line number
        else:
            lnotab.append(line_info[1]-lines[lidx-1][1])
            lnotab.append(line_info[0]-lines[lidx-1][0])

    lnotab = bytes(lnotab)
    return (exec_flow, lnotab)

def parse_opcode_string(string: str):
    return parse_opcode_file(__import__('io').StringIO(string))


def get_definition_map() -> dict[str, tuple[int, bool]]:
    _opc_path = os.path.split(sys.executable)[0]+"\\include\\opcode.h"
    if not os.path.isfile(_opc_path):
        return None
    
    with open(_opc_path, 'r') as fp:
        return parse_definition_file(fp)

def calc_stacksize(tokens: list[tuple[str, int]]) -> int:
    max_size = 0
    stacksize = 0

    for instruction, argument in tokens:
        instruction = opcodes[instruction][0]
        if argument != None:
            stacksize += _opcode.stack_effect(instruction, argument)
        else:
            stacksize += _opcode.stack_effect(instruction)
        if stacksize > max_size:
            max_size = stacksize
    return max_size

def assemble_instructionflow(flow: list[tuple[str, int]]) -> bytes:
    bytecode = []
    for instruction in flow:
        bytecode.append(opcodes[instruction[0]][0])
        bytecode.append(instruction[1] if instruction[1] else 0)

    return bytes(bytecode)

if not (opcodes := get_definition_map()):
    print("[ERROR]: Failed generating opcode-map.")

def parse_function_signature(signature: str):
    # example: "functionname(argument1, argument2, argument3)"
    signature = signature.strip().replace(' ','')
    name = ""
    arguments = []
    buffer = ""
    depth = 0
    ignore_metadata = False

    for idx, c in enumerate(signature):
        if c == '(':
            name = buffer
            buffer = ''
            depth += 1
        elif c == ',' and depth == 1:
            arguments.append(buffer)
            buffer = ''
            ignore_metadata = False
        elif c == ':':
            ignore_metadata = True
        elif c == ')':
            if depth == 0:
                raise Exception("EOL: closing non-opened bracket.")
            depth -= 1
            if depth == 0:
                break
        elif not ignore_metadata:
            buffer += c

    if buffer:
        arguments.append(buffer)

    return name, tuple(arguments)




def make_function(
    argcount: int,
    posonlyargcount: int,
    kwonlyargcount: int,
    nlocals: int,
    stacksize: int,
    flags: int,
    codestring: bytes,
    constants: tuple,  # constant values starting with (None,)
    names: tuple, # (Function names etc.)
    varnames: tuple, # variable names including parameters
    filename: str,
    name: str, # function name
    firstlineno: int,
    lnotab: bytes,
    globals: dict):

    _tcode = types.CodeType(argcount,
        posonlyargcount,
        kwonlyargcount,
        nlocals,
        stacksize,
        flags,
        codestring,
        constants,
        names,
        varnames,
        filename,
        name,
        firstlineno,
        lnotab)
    return types.FunctionType(_tcode, globals)


# decorator inline assembly
# doesnt support *args or **kwargs

def pasm(signature: str, code: str, locals, constants, functions, globals={}):
    tokens, lnotab = parse_opcode_string(code)
    code = assemble_instructionflow(tokens)
    function_name, function_arguments = parse_function_signature(signature)

    compiled = make_function(
        argcount=len(function_arguments),
        posonlyargcount=0,
        kwonlyargcount=0,
        nlocals=len(locals)+len(function_arguments),
        stacksize=calc_stacksize(tokens),
        flags=0,
        codestring=code,
        constants=constants,
        names=functions,
        varnames=function_arguments+locals,
        filename="<string>",
        name=function_name,
        firstlineno=1,
        lnotab=lnotab,
        globals=globals)


    def wrap(func):
        func(compiled)

    return wrap

if __name__ == '__main__' and opcodes:
    if len(sys.argv) != 2:
        sys.exit("Usage: python {} [path-to-pyasm-file]".format(sys.argv[0]))
    
    if not os.path.isfile(sys.argv[1]):
        sys.exit("[ERROR]: File does not exist.")
    
    with open(sys.argv[1], 'r') as fp:
        if not (parsed := parse_opcode_file(fp)):
            sys.exit(2)

    flow, lnotab = parsed
    print("lnotab:", str(lnotab))
    print("Code:", str(assemble_instructionflow(flow)))
