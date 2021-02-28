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