from src.instructions import Instruction


"""
Class for handling sets of instructions
"""
class InstructionSet:
    _instructions = []
    _id = ""
    _debug = False
    _instructions_initialized = False

    def __init__(self, name, debug=False):
       self._id = name
       self._debug = debug

    def append(self, i):
        if type(i) == list:
            self._instructions = self._instructions + i
        else:
            self._instructions.append(i)

    def clear(self):
        self._instructions = []

