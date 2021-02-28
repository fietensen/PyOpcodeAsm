# PyOpcodeAsm
Python opcode assembler / Python inline-assembly

## Variables defined:
- opcodes: `{opcode_name: (opcode_number, requires_parameter), ...}`

## Functions defined:
- `parse_definition_file(fp) ->  dict[str, tuple[int, bool]]`
    - fp => file object for python's opcode.h file
    - returns `opcodes`-map
- `parse_opcode_file(fp) -> tuple[list[tuple[str, int]], bytes]`
    - fp => file object for ".pasm" file containing instructions
    - returns `([(instruction_name, parameter), ...], lnotab)`
    - returns `(code_tokens, lnotab)`
- `parse_opcode_string(string) -> tuple[list[tuple[str, int]], bytes]`
    - string => instruction code
    - returns instruction tokens & lnotab, same format as `parse_opcode_file`
- `get_definition_map() -> dict[str, tuple[int, bool]]`
    - automates the opening/parsing of the opcode.h file
    - returns `opcodes`-map
- `calc_stacksize(tokens) -> int`
    - calculates the highest amount of stack space required when running the tokens
- `assemble_instructionflow(tokens) -> bytes`
    - compiles tokens to bytecode
- `parse_function_signature(signature: str) -> tuple[str, list[str]]`
    - parses function signature like `"my_function(arg1: int, arg2, arg3: list[int])"`
    - returns `(function_name, [argument1_name, argument2_name, ...])`
- `make_function(...) -> callable function`
    - required parameters:
        - `argcount: int => number of function arguments`
        - `posonlyargcount: int => number of *args, only 0 supported`
        - `kwonlyargcount: int => number of **kwargs, only 0 supported`
        - `nlocals: int => number of local variables, includes parameters`
        - `stacksize: int => stack size required for function`
        - `flags: int => code object flags, can be left 0`
        - `codestring: bytes => compiled python bytecode`
        - `constants: tuple => constant values for function`
        - `names: tuple[str] => function names to be referenced in function`
        - `varnames: tuple[str] => variable names, includes function arguments`
        - `filename: str => function source filename, can be set to "<string>"`
        - `firstlineno: int => starting line number, can be set to 0`
        - `lnotab: int => encoded mapping of bytecode<->line offsets`
        - `globals: dict => global variables the function has access to`
    - returns function that you can call

## Decorators defined:
- `pasm`
    - arguments:
        - `signature: str => function signature string`
        - `code: str => instruction string to be compiled`
        - `locals: tuple => tuple of local variables defined, remember func arguments are automatically prepended`
        - `constants: tuple => tuple of constants used in function`
        - `functions: tuple => tuple of function names accessible from the function`
        - `globals: dict => global variables the function has access to`


## Examples:

### Using the inline assembly:
```python
# Original function:
def my_function(a):
    b = 5
    print(a, b)
my_function(3)
```

```python
# Inline assembly recreation
import poa

@poa.pasm(
    signature="my_function(a)",
    code=
    """
    1:
        LOAD_CONST      1
        STORE_FAST      1


    2:
        LOAD_GLOBAL     0
        LOAD_FAST       0
        LOAD_FAST       1

        CALL_FUNCTION   2
        POP_TOP

        LOAD_CONST      0
        RETURN_VALUE
    """,
    locals=('b',),
    constants=(None, 5,),
    functions=('print',),
    globals={'print': print})

def run(function):
    function(3)
```