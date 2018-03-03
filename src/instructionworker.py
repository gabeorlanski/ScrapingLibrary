import multiprocessing as mp
import sys
import os
import copy

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
		instructions = []
		for i in self.instructions_dict:
			instructions.append(Instruction(**i))
		while True:
			
			next_task = self.task_queue.get()
			
			if next_task is None:
				if self._debug:
					print(self._id + " received poison pill")
				
				# Poison pill means shutdown
				self.task_queue.task_done()
				break
			key, data = next_task
			if self._debug:
				print(self._id + " received data for key: '" + str(key) + "'. Applying instructions to the data...")
			
			# Apply the instructions onto the data from the queue
			if not self.testing:
				result = [None for i in instructions]
				for i in range(len(instructions)):
					rtr = instructions[i](data)
					try:
						result[i] = {
							"name": instructions[i].getName(), 'data':rtr[1]
						}
					except Exception as e:
						if self._debug:
							print(
								self._id + " ran into Exception '{}' when trying to apply instruction {} to {}".format(
									str(e), instructions[i].getName(), key))
			else:
				result = []
				for i in self.testing:
					result.append(instructions[i](data))
			if self._debug:
				print(self._id + " putting the results into the result queue...")
			self.result_queue.put([key, result])
			self.task_queue.task_done()
