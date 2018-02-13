import multiprocessing as mp
from instructions import Instruction

class Scraper:
    _cores = 0
    _data = None
    _xpaths = None
    _debug = False

    def __init__(self, cores=0, debug=False):
        self._cores = cores
        self._debug = debug

    def add_xpaths(self, paths):
        if type(paths) != list:
            raise TypeError("Expected list, got instead " + str(type(paths)))

        for i, z in zip(paths,range(len(path))):
            # Checking to make sure the values passed are of the correct form and have the correct fields
            if "name" not in 
            continue


