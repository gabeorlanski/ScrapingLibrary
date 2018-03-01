import multiprocessing as mp
import sys
import os
import copy
if r'\tests' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import Instruction


class InstructionWorker(mp.Process):

    def __init__(self, task_queue, result_queue, instructions,testing_mode=None):
        mp.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.instructions_dict = instructions
        self.testing = testing_mode

    def run(self):
        instructions = []
        for i in self.instructions_dict:

            instructions.append(Instruction(**i))
        while True:

            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                self.task_queue.task_done()
                break
            key, data = next_task
            if not self.testing:
                result = [None for i in instructions]
                for i in range(len(instructions)):
                    result[i] = instructions[i](data)
            else:
                result = []
                for i in self.testing:
                    result.append(instructions[i](data))
            self.result_queue.put((key,result))
            self.task_queue.task_done()