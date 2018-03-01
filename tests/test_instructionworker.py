from unittest import TestCase
import multiprocessing as mp
import sys
import os
import random

if r'\tests' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import Instruction
from src.instructionworker import InstructionWorker


class TestInstructionWorker(TestCase):

    def setUp(self):
        filename = ["test_html_1.html", "test_html_2.html", "test_html_3.html", "test_html_4.html", "test_html_5.html", "test_html_6.html",
                    "test_html_7.html", "test_html_8.html", "test_html_9.html", "test_html_10.html"]
        self.htmls = []

        for f, c in zip(filename, range(len(filename))):
            html = open(os.getcwd() + r'\tests\instructionworker_test_html\\' + f).read()
            for i in range(1, 25):
                self.htmls.append(("file_" + str(c+1), html))
        random.shuffle(self.htmls)
        self.instructions = []
        self.instructions.append(Instruction("//p", "basic", text=True).get_init_dict())
        self.instructions.append(
            Instruction("//div[@class='test_parent']", "parent", text=True, children=[Instruction("./div[@class='test_child']", "child", text=True)]).get_init_dict())
        self.instructions.append(Instruction("//a", "attrib", attrib={'link': 'href'}).get_init_dict())

    def test_basic(self):
        q = mp.JoinableQueue()
        r = mp.JoinableQueue()
        workers = 4
        consumers = [InstructionWorker(q, r,self.instructions,[0]) for i in range(workers)]
        for c in consumers:
            c.start()

        for i in range(len(self.htmls)):
            k,d = self.htmls[i]
            k = k+ "-"+str(i)
            q.put((k,d))

        for c in consumers:
            q.put(None)

        q.join()
        while not r.empty():
            result = r.get()
            k = result[0]
            d = result[1]
            k_num = int(k.split("-")[0].split("_")[1])
            d_num = int(d[0][1]["result_1"]["basic"].split("_")[1])
            self.assertEqual(k_num,d_num)