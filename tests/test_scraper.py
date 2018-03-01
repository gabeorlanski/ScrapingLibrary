from unittest import TestCase
import sys
import os
from lxml import etree
from io import StringIO

if r'\tests' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.scraper import Scraper


class TestScraper(TestCase):

    def test_basic_addXpaths(self):
        scraper = Scraper(debug=True)
        xpaths = [
            {"name":"Basic_Test", "raw":"//div", "children":[],"options":{}},
            {"name":"Child_Test", "raw":"//div", "children":[{"name":"Basic_Child", "raw":"//div", "children":[],"options":{}}],"options":{}},
            {"name": "Options_Test", "raw": "//div", "children": [], "options": {"text":True}}

        ]

        scraper.addInstructions(xpaths)

        self.assertDictEqual(scraper._instructions[0].get_init_dict(),{"name":"Basic_Test", "raw":"//div", "children":[],"options":{}})
        self.assertDictEqual(scraper._instructions[1].get_init_dict(),{"name":"Child_Test", "raw":"//div", "children":[{"name":"Basic_Child", "raw":"//div", "children":[],"options":{}}],"options":{}})
        self.assertDictEqual(scraper._instructions[2].get_init_dict(),{"name": "Options_Test", "raw": "//div", "children": [], "options": {"text":True}})
