import multiprocessing as mp
import sys
import os
from collections import defaultdict

if r'\tests' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import Instruction


class InstructionWorker(mp.Process):
    def __init__(self, task_queue, result_queue, instructions, worker_id, debug=False, testing_mode=None):
        mp.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.instructions_dict = instructions
        self.testing = testing_mode
        self._debug = debug
        self._id = worker_id

    def run(self):
        instructions = defaultdict(list)
        for k in self.instructions_dict.keys():
            for i in self.instructions_dict[k]:
                instructions[k].append(Instruction(**i))

        while True:

            next_task = self.task_queue.get()

            if next_task is None:
                if self._debug:
                    print(self._id + " received poison pill")

                # Poison pill means shutdown
                self.task_queue.task_done()
                break
            key, data, instruct_set,link = next_task
            instructions_init_dicts = {i.getName(): i.get_init_dict(True) for i in instructions[instruct_set]}
            if self._debug:
                print(self._id + " received data for key: '" + str(key) + "'. Applying getListings to the data...")

            # Apply the getListings onto the data from the queue
            if not self.testing:
                result = {"metadata":{"link":link, "instructions_applied":instructions_init_dicts,"data_keys":self.find_data_keys(instructions_init_dicts)}}
                for i in range(len(instructions[instruct_set])):

                    rtr = instructions[instruct_set][i](data,key)

                    try:
                        result["metadata"][instructions[instruct_set][i].getName()+"_resultcount"] = len(rtr[1].keys())
                        result[instructions[instruct_set][i].getName()] = rtr[1]
                    except Exception as e:
                        if self._debug:
                            print(self._id + " ran into Exception '{}' when trying to apply instruction {} to {}".format(str(e),
                                    instructions[instruct_set][i].getName(), key))
            else:
                result = []
                for i in self.testing:
                    result.append(instructions[instruct_set][i](data))
            if self._debug:
                print(self._id + " putting the results into the result queue...")
            self.result_queue.put([key, result,instruct_set])
            self.task_queue.task_done()

    def find_data_keys(self,i):
        rtr = {}
        for istr in i.keys():
            keys = []
            has_data = False
            has_text =False
            if "attrib" in i[istr]:
                has_data = True
                for a in i[istr]["attrib"].keys():
                    keys.append(a)
            if "text" in i[istr]:
                has_data = True
                has_text = True
            children = {}
            if i[istr]["children"]:
                children = self.find_data_keys(i[istr]["children"])
            if children:
                has_data = True
            if has_data:
                rtr[istr] = {"keys":keys,"children":children,"text":has_text}
        return rtr