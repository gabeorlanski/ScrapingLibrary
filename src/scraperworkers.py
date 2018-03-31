import multiprocessing as mp
import sys
import os
from collections import Counter

if r'\src' in os.getcwd() or r'\src' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))
from src import asyncrequester


class ContinuousRequester(mp.Process):

    def __init__(self, task_queue, result_queue, processed_queue, rules_dict, stop_conditions, number_other_workers, worker_id,threshold=1,
                                                                                                                              debug=False, \
                                                                                                                             testing_mode=None):
        mp.Process.__init__(self)
        self._tasks = task_queue
        self._results = result_queue
        self._processed = processed_queue
        self._rules = rules_dict
        self._counts = Counter(list(rules_dict.keys()))
        self._threshold = threshold
        self._stop_conditions = stop_conditions
        self._num_other_workers = number_other_workers
        self._id = worker_id
        self._debug = debug

    def run(self):
        stop_triggered = False
        poison_tasks = False
        new_links = []

        while True:
            next_task = self._results.get()

            if next_task is None:
                if self._debug:
                    print(self._id + " received poison pill")

                # Poison pill means shutdown
                self._results.task_done()
                break

            key, data, instruction_set = next_task

            if self._debug:
                print(self._id + " received data for key: '" + str(key) + "'. Applying instructions to the data...")

            if stop_triggered:
                self._processed.put([key, data, instruction_set])

                if len(new_links) != 0:
                    self.get_links(new_links)
                    new_links = []
                elif self._results.empty():
                    self._results.put(None)
                elif not poison_tasks:
                    for i in range(self._num_other_workers):
                        self._tasks.put(None)
                    poison_tasks = True
            else:
                if "instructionSet" in self._stop_conditions and "dictKey" in self._stop_conditions:
                    if self._stop_conditions["instructionSet"] == instruction_set and self._stop_conditions["dictKey"] == key:
                        stop_triggered = True
                elif "dictKey" in self._stop_conditions:
                    if self._stop_conditions["dictKey"] == key:
                        stop_triggered = True
                elif "instructionSet" in self._stop_conditions:
                    if self._stop_conditions["instructionSet"] == instruction_set:
                        stop_triggered = True

                self._counts[instruction_set] += 1
                p, t = self._rules[instruction_set]["apply"](key,data,instruction_set)
                self._processed.put(p)

                for i in range(len(t)):
                    if "keyApply" in self._rules[instruction_set]:
                        t[i]["dictKey"] = t[i]["dictKey"] + self._rules[instruction_set]["keyApply"] + str(self._counts[instruction_set])
                    new_links.append(t[i])

                if len(new_links) >= self._threshold:
                    self.get_links(new_links)
                    new_links = []

    def get_links(self,links):
        links_with_set = {}
        for d in links:
            links_with_set[d["dictKey"]] = {"instructionSet": d["instructionSet"], "link": d["url"]}
        page_data = asyncrequester.Scraper(request_params=links).return_results()
        for data_key in range(len(page_data)):
            k = page_data[data_key]["key"]
            d = page_data[data_key]['response'].decode()
            self._tasks.put([k, d,links_with_set[k]["instructionSet"],links[k]["link"]])
        self._tasks.join()


