from unittest import TestCase
import sys
import os
from lxml import etree
from io import StringIO


if r'\tests' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import *


class TestInstruction(TestCase):
    def setUp(self):
        import pprint
        self.pp = pprint.PrettyPrinter(indent=4)
        self.basic_html = open(os.getcwd() + r'\tests\instruction_test_html\basic_call.html').read()
        self.complex_html = open(os.getcwd() + r'\tests\instruction_test_html\complex_tests.html').read()
        self.maxDiff = None

    def test_init(self):
        test = Instruction("//div", "test_name", [Instruction("//a"), Instruction("//b")], True, {"test_attrib_key": "test_attrib"}, True)
        self.assertEqual(test._raw, "//div")
        self.assertEqual(test._name, "test_name")
        self.assertEqual(test._children[0]._raw, "//a")
        self.assertEqual(test._children[1]._raw, "//b")
        self.assertEqual(test._children[1]._raw, "//b")
        self.assertTrue(test._text)
        self.assertDictEqual(test._attrib, {"test_attrib_key": "test_attrib"})
        self.assertTrue(test._getdata)

        test_b = Instruction("//div", "test_b_name")
        self.assertEqual(test_b._raw, "//div")
        self.assertEqual(test_b._name, "test_b_name")
        self.assertEqual(test_b._children, [])
        self.assertFalse(test_b._text)
        self.assertEqual(test_b._attrib, {})
        self.assertFalse(test_b._getdata)

    def test_addChild(self):
        test_parent = Instruction("parent")
        test_child = Instruction("child")
        test_error = "error"
        self.assertEqual(len(test_parent._children), 0)
        test_parent.addChild(test_child)
        self.assertEqual(len(test_parent._children), 1)
        self.assertEqual(test_parent._children[0]._raw, "child")
        with self.assertRaises(TypeError):
            test_parent.addChild(test_error)

    def test_basic_call(self):
        # TESTING BASIC INSTRUCTION
        basic = Instruction("//p", "test", text=True)
        success, returned= basic(self.basic_html)
        self.assertTrue(success)
        self.assertDictEqual(returned, {'result_1': {'test': '<p>Test Basic</p>', 'num_children': 0, 'children': []}})

    def test_no_results(self):
        # TESTING NO RESULTS
        nothing = Instruction("//div[@class='blah']", "nothing")
        success,returned = nothing(self.basic_html)
        self.assertIsNone(returned)
        self.assertFalse(success)

    def test_child(self):
        # TESTING CHILD
        parent_a = Instruction("//div[@class='single_parent']", "parent", text=True)
        child_a = Instruction("./div[@class='single_child']", "child", text=True)
        parent_a.addChild(child_a)
        success_a,rslt_a = parent_a(self.basic_html)
        self.assertTrue(success_a)
        self.assertDictEqual(parent_a.get_format(),
                             {'result_1': {'parent': 'Text data', 'num_children': 1, 'children': [{'result_1': {'child': 'Text data'}}]}})

        self.assertDictEqual(rslt_a, {
            'result_1': {'children': [{'child_1': {'children': [], 'child': 'Child', 'num_children': 0}}], 'parent': 'Parent', 'num_children': 1}
        })

    def test_child_no_result(self):
        # TESTING CHILD NO RESULT
        parent_b = Instruction("//div[@class='single_parent']", "parent", text=True)
        child_b = Instruction("./h1", "child", text=True)
        parent_b.addChild(child_b)
        success_b,rslt_b= parent_b(self.basic_html)
        self.assertTrue(success_b)
        self.assertDictEqual(rslt_b, {
            'result_1': {
                'parent': 'Parent', 'num_children': 1, 'children': []
            }
        })

    def test_multi_element(self):
        # TESTING MULTI ELEMENT
        multi = Instruction("//div[@class='multi_parent']", "multi", text=True)
        success_m,rslt_m = multi(self.basic_html)
        self.assertTrue(success_m)
        self.assertDictEqual(rslt_m, {
            'result_1': {'children': [], 'multi': 'Multi Number 1', 'num_children': 0},
            'result_2': {'children': [], 'multi': 'Multi Number 2', 'num_children': 0}
        })

    def test_attributes(self):
        # TESTING ATTRIBUTES
        attrib = Instruction("//a", "attrib", attrib={'link': 'href'})
        success_c,rslt_c = attrib(self.basic_html)
        self.assertTrue(success_c)
        self.assertDictEqual(rslt_c, {'result_1': {'link': 'www.reddit.com', 'children': [], 'num_children': 0}})

    def test_child_multi(self):
        # TESTING MULTI CHILDREN
        a = Instruction("//div[@class='multi_parent']", "parent", text=True)
        b = Instruction("./div[@class='multi_child']", "child", text=True)
        a.addChild(b)
        worked,rslt = a(self.basic_html)

        self.assertTrue(worked)
        self.assertEqual(type(rslt), dict)
        self.assertDictEqual(rslt, {
            'result_2'   : {
                'children': [{'child_1': {'children': [], 'child': 'Child Number 2', 'num_children': 0}}], 'num_children': 1,
                'parent'  : 'Multi Number 2'
            }, 'result_1': {
                'children'        : [{
                    'child_2': {'children': [], 'child': 'Child Number 1 2', 'num_children': 0},
                    'child_1': {'children': [], 'child': 'Child Number 1', 'num_children': 0}
                }], 'num_children': 1, 'parent': 'Multi Number 1'
            }
        })

    def test_nested_child(self):
        a = Instruction("//div[@class='nested_children']", "parent", text=True)
        b = Instruction("//div[@class='nested_child']", "child", text=True)
        c = Instruction("//p[@class='nested_child']", "sub_child", text=True)
        b.addChild(c)
        a.addChild(b)
        worked, returned =a(self.complex_html)
        self.assertTrue(worked)
        self.assertDictEqual(returned, {
            'result_1': {
                'children'  : [{
                    'child_1': {
                        'children': [{'sub_child_1': {'sub_child': 'Sub Child', 'children': [], 'num_children': 0}}], 'child': 'Child',
                        'num_children': 1
                    }
                }], 'parent': 'Parent', 'num_children': 1
            }
        })

    def test_backup(self):
        # TESTING BASIC INSTRUCTION
        basic = Instruction("//div[@class='test']", "test", text=True, backup_xpaths=["//p"])
        success,returned= basic(self.basic_html)
        self.assertTrue(success)
        self.assertDictEqual(returned, {'result_1': {'test': '<p>Test Basic</p>', 'num_children': 0, 'children': []}})

    def test_multi_child_backup(self):
        # TESTING MULTI CHILDREN
        a = Instruction("//div[@class='doesnotexist']", "parent", text=True, backup_xpaths=["//div[@class='multi_parent']"])
        b = Instruction("//div[@class='test2iguess']", "child", text=True, backup_xpaths=["./div[@class='multi_child']"])
        a.addChild(b)
        worked, rslt= a(self.basic_html)
        self.assertTrue(worked)
        self.assertEqual(type(rslt), dict)
        self.assertDictEqual(rslt, {
            'result_2'   : {
                'children': [{'child_1': {'children': [], 'child': 'Child Number 2', 'num_children': 0}}], 'num_children': 1,
                'parent'  : 'Multi Number 2'
            }, 'result_1': {
                'children'        : [{
                    'child_2': {'children': [], 'child': 'Child Number 1 2', 'num_children': 0},
                    'child_1': {'children': [], 'child': 'Child Number 1', 'num_children': 0}
                }], 'num_children': 1, 'parent': 'Multi Number 1'
            }
        })

    def test_dict_generator_nestedchild(self):
        # c is the child of b which is the child of b
        c = generate_instruction_dict("./p[@class='nested_child']", "sub_child", text=True)
        b = generate_instruction_dict("./div[@class='nested_child']", "child", text=True,children=[c])
        a = generate_instruction_dict("//div[@class='nested_children']", "parent", text=True,children=[b])
        self.assertEqual(len(b["children"]),1)
        self.assertEqual(len(c["children"]),0)
        self.assertEqual(len(a["children"]), 1)
        self.assertEqual(len(a["children"][0]["children"]),1)
        self.assertEqual(len(a["children"][0]["children"][0]["children"]),0)
        instr = Instruction(**a)

        self.assertEqual(instr.getName(), "parent")
        self.assertEqual(len(instr._children), 1)
        self.assertEqual(instr._children[0].getName(),"child")
        self.assertEqual(instr._children[0]._children[0].getName(),"sub_child")

        worked, returned = instr(self.complex_html)
        self.assertTrue(worked)
        self.assertDictEqual(returned, {
            'result_1': {
                'children'  : [{
                    'child_1': {
                        'children'    : [{'sub_child_1': {'sub_child': 'Sub Child', 'children': [], 'num_children': 0}}], 'child': 'Child',
                        'num_children': 1
                    }
                }], 'parent': 'Parent', 'num_children': 1
            }
        })
