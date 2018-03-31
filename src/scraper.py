import multiprocessing as mp
import sys
import os
import json
from collections import defaultdict
from time import sleep
if r'\src' in os.getcwd() or r'\src' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import Instruction, generate_instruction_dict
from src import asyncrequester
from src.instructionworker import InstructionWorker
from src.scraperworkers import ContinuousRequester


def validateXpathDict(xpath, path_to_current, debug):
    keys = xpath.keys()
    try:
        path_to_current_str = "->".join(path_to_current + [xpath["name"]])
    except KeyError:
        raise ValueError("Missing the key 'name' in the xpath located at: " + "==>".join(path_to_current) + "->No Name Found!")

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
    _instruction_sets = defaultdict(list)
    _debug = False
    _links = []
    _backuplinks = []
    _continuous_adding = False

    def __init__(self, cores=1, debug=False, continuous_adding=False):
        self._cores = cores
        self._debug = debug
        self._continuous_adding = continuous_adding

    def addInstructions(self, instr, instruct_set):
        """
        :param instr: List of Instruction dictionaries you want to add
        :type instr: [dict]
        :param instruct_set: id for the instruction set you want to add the instruction to
        :type instruct_set: str
        """

        # ERROR CHECKING
        if type(instr) != list:
            raise TypeError("Expected list, got instead " + str(type(instr)))
        if len(instr) == 0:
            raise ValueError("Paths was passed an empty list")
        if type(instr[0]) != dict and type(instr[0]) != Instruction:
            raise TypeError("Expected instr to be a list of dicts or instructions, got instead " + str(type(instr)) + " of " + str(type(instr[0])))
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
            self._instruction_sets[instruct_set].append(instruction_init_flags)

    def addLinks(self, links, append=False):
        """
        :param links: List of dictionaries that follow this format: {"dictKey":How you want to categorize this link, "url":self explanatory,
        "headers": any headers you want to send with the link (WIP), "instructionSet": The instruction set you want to be applied to this link}
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
            raise TypeError("Expected instr to be a list of dicts, got instead " + str(type(links)) + " of " + str(type(links[0])))
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
        links_with_set = {}
        for d in self._links:
            links_with_set[d["dictKey"]] = {"instructionSet": d["instructionSet"], "link": d["url"]}
        page_data = asyncrequester.Scraper(request_params=self._links).return_results()
        q = mp.JoinableQueue()
        r = mp.JoinableQueue()
        # p = mp.JoinableQueue()

        if self._debug:
            print("Number of cores to use: " + str(self._cores))

        # if not self._continuous_adding:
        workers = self._cores

        # else:
        #     if self._cores == 1:
        #         raise ValueError("cores cannot must be > 1 when continuous_adding is True")
        #     workers = self._cores - 1

        consumers = [InstructionWorker(q, r, self._instruction_sets, "worker_num_" + str(i), debug=self._debug) for i in range(workers)]

        # if self._continuous_adding:
        #     consumers.append(
        #             ContinuousRequester(q, r, p, self._rules_dict, self._stop_conditons, workers, "ContinuousRequester_{}".format(workers + 1),
        #                                 self._threshold, debug=self._debug))

        if self._debug:
            print("Number of workers: " + str(len(consumers)))
        for c in consumers:
            c.start()
        if self._debug:
            print("Number of pages in page_data: " + str(len(page_data)))
        print("Putting page data into queue...")
        for data_key in range(len(page_data)):
            # import io
            # with io.open(page_data[data_key]["key"]+".html", "w", encoding="utf-8") as f:
            #     print("DELETE THE WRITING OF EVERY HTML PAGE!!!")
            #     f.write(str(page_data[data_key]['response']))
            k = page_data[data_key]["key"]
            d = page_data[data_key]['response'].decode()
            q.put([k, d, links_with_set[k]["instructionSet"], links_with_set[k]["link"]])
        if self._debug:
            print("Putting poison pill into the workers' queue")

        for c in consumers:
            q.put(None)


        q.join()


        result_data = {}
        if self._debug:
            print("Retrieving results from the result queue")
        # if self._continuous_adding:
        #     results_done = p
        # else:
        #     results_done = r
        # while not results_done.empty():
        #     result = results_done.get()
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
                try:
                    tmp_dict_data[k["name"]] = {**k["data"], "num_results": len(list(k["data"].keys()))}
                except:
                    pass
            if tmp_dict_data:
                result_data[key] = tmp_dict_data

        with open("test_data.json", 'w') as fp:
            json.dump(result_data, fp, indent=4, sort_keys=True)

    def continuous_params(self, rules, stop_conditions, threshold=1):
        self._rules_dict = rules
        self._stop_conditons = stop_conditions
        self._threshold = threshold
