import multiprocessing as mp
import sys
import os
import json

if r'\src' in os.getcwd() or r'\src' in os.getcwd():
	sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
	os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import Instruction, generate_instruction_dict
from src import asyncrequester
from src.instructionworker import InstructionWorker


def validateXpathDict(xpath, path_to_current, debug):
	keys = xpath.keys()
	try:
		path_to_current_str = "->".join(path_to_current + [xpath["name"]])
	except KeyError:
		raise ValueError(
			"Missing the key 'name' in the xpath located at: " + "==>".join(path_to_current) + "->No Name Found!")
	
	if debug:
		print("Validating Xpath Dict @ " + path_to_current_str)
	
	path_to_current.append(xpath["name"])
	
	if "xpath" not in keys:
		raise ValueError("Missing the key 'raw' in the xpath located at: " + path_to_current_str)
	
	if "children" not in keys:
		raise ValueError("Missing the key 'children' in the xpath located at: " + path_to_current_str)
	if type(xpath["children"]) != list:
		raise TypeError("the type of the value of the 'raw' key must be a list at xpath: " + path_to_current_str)
	
	# if "options" not in keys:
	#     raise ValueError("Missing the key 'options' in the xpath located at: " + path_to_current_str)
	# if type(xpath["options"]) != dict:
	#     raise TypeError("the type of the value of the 'options' key must be a dict at xpath: " + path_to_current_str)
	
	for c in xpath["children"]:
		validateXpathDict(c, path_to_current, debug)


class Scraper:
	_cores = 0
	_data = None
	_instructions = []
	_debug = False
	_links = []
	_backuplinks = []
	
	def __init__(self, cores=1, debug=False):
		self._cores = cores
		self._debug = debug
	
	def addInstructions(self, instr):
		"""
		:param instr: List of Instruction dictionaries you want to add
		:type instr: [dict]
		"""
		
		# ERROR CHECKING
		if type(instr) != list:
			raise TypeError("Expected list, got instead " + str(type(instr)))
		if len(instr) == 0:
			raise ValueError("Paths was passed an empty list")
		if type(instr[0]) != dict and type(instr[0]) != Instruction:
			raise TypeError(
				"Expected instr to be a list of dicts or instructions, got instead " + str(type(instr)) + " of " + str(
					type(instr[0])))
		if type(instr[0]) == dict:
			dict_constructor = True
		else:
			dict_constructor = False
		if self._debug:
			print("Number of Paths: " + str(len(instr)))
		
		for i, z in zip(instr, range(len(instr))):
			# Checking to make sure the values passed are of the correct form and have the correct fields
			if not dict_constructor:
				instruction_init_flags = i.get_init_dict()
			else:
				validateXpathDict(i, ["TOP LEVEL"], self._debug)
				instruction_init_flags = i
			
			if self._debug:
				print("instruction_init_flags: " + str(instruction_init_flags))
			self._instructions.append(instruction_init_flags)
	
	def addLinks(self, links, append=False):
		"""
		:param links: List of dictionaries that follow this format: {"dictKey":How you want to categorize this link, "url":self explanatory,
		"headers": any headers you want to send with the link (WIP)}
		:type links: [dict]
		:param append: do you want to overwrite or append the list of links
		:type append: bool
		"""
		
		# ERROR CHECKING
		if type(links) != list:
			raise TypeError("Expected list, got instead " + str(type(links)))
		if len(links) == 0:
			raise ValueError("Paths was passed an empty list")
		if type(links[0]) != dict:
			raise TypeError(
				"Expected instr to be a list of dicts, got instead " + str(type(links)) + " of " + str(type(links[0])))
		if append:
			self._links = self._links + links
		else:
			if len(self._links) != 0:
				raise ValueError("Call clearLinks() before adding new links or make append True!!")
			self._links = links
	
	def clearLinks(self):
		"""
		Call this to clear the links before adding more links
		"""
		self._backuplinks = self._backuplinks + self._links
		self._links = []
	
	def run(self, links=None):
		if not links and len(self._links) == 0:
			raise AttributeError("No links were passed, and there currently no links in self._links")
		
		if links:
			self.addLinks(links)
		
		page_data = asyncrequester.Scraper(request_params=self._links).return_results()
		q = mp.JoinableQueue()
		r = mp.JoinableQueue()
		
		if self._debug:
			print("Number of cores to use: " + str(self._cores))
		
		workers = self._cores
		consumers = [InstructionWorker(q, r, self._instructions, "worker_num_" + str(i), debug=self._debug) for i in
		             range(workers)]
		
		if self._debug:
			print("Number of workers: " + str(len(consumers)))
		
		for c in consumers:
			c.start()
		
		if self._debug:
			print("Number of pages in page_data: " + str(len(page_data)))
			print("Putting page data into queue...")
		for data_key in range(len(page_data)):
			k = page_data[data_key]["key"]
			d = page_data[data_key]['response'].decode()
			q.put((k, d))
		
		if self._debug:
			print("Putting poison pill into the workers' queue")
		for c in consumers:
			q.put(None)
		
		q.join()
		
		result_data = {}
		if self._debug:
			print("Retrieving results from the result queue")
		while not r.empty():
			result = r.get()
			key = result[0]
			d = result[1]
			# print(k)
			# Put all of the results into one dictionary
			# tmp[k] = {}
			# for i in d:
			# 	tmp[k][i[0]] = i[1]
			tmp_dict_data = {}
			for k in d:
				tmp_dict_data[k["name"]] = {**k["data"], "num_results": len(list(k["data"].keys()))}
			result_data[key] = tmp_dict_data


if __name__ == "__main__":
	s = Scraper(cores=1, debug=True)
	links = [
		{"headers": {}, "dictKey": "random1", "url": "https://en.wikipedia.org/wiki/Siah_Bisheh,_Chalus"},
		{"headers": {}, "dictKey": "random2", "url": "https://en.wikipedia.org/wiki/PCM30"},
		{"headers": {}, "dictKey": "random3", "url": "https://en.wikipedia.org/wiki/John_Shaw_(public_servant)"},
		{"headers": {}, "dictKey": "random4", "url": "https://en.wikipedia.org/wiki/Monetary_inflation"},
		{"headers": {}, "dictKey": "random5",
		 "url": "https://en.wikipedia.org/wiki/2017_BWF_World_Championships_%E2%80%93_Women%27s_singles"}]
	
	instructions = [generate_instruction_dict("//h1[@class='firstHeading']", "title", text=True, etree_text=True),
	                generate_instruction_dict("//p", "text", text=True)]
	s.addInstructions(instructions)
	s.run(links)
