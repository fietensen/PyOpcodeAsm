import poa

with open('test.pasm', 'r') as fp:
    tokens, lnotab = poa.parse_opcode_file(fp)
    code = poa.assemble_instructionflow(tokens)

compiled = poa.make_function(
    argcount=1,
    posonlyargcount=0,
    kwonlyargcount=0,
    nlocals=2,
    stacksize=poa.calc_stacksize(tokens),
    flags=0,
    codestring=code,
    constants=(None, 5,),
    names=("print",),
    varnames=('a','b',),
    filename="<string>",
    name="compiled",
    firstlineno=0,
    lnotab=lnotab,
    globals={'print': print})

compiled(3)