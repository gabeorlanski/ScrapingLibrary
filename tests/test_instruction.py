from unittest import TestCase
import sys
import os
from lxml import etree
from io import StringIO

if r'\tests' in os.getcwd():
	sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
	os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.instructions import Instruction


class TestInstruction(TestCase):
	def setUp(self):
		self.basic_html = open(os.getcwd()+r'\tests\instruction_test_html\basic_call.html').read()

	def test_init(self):
		test = Instruction("//div", "test_name", [Instruction("//a"), Instruction("//b")], True, {"test_attrib_key":"test_attrib"}, True)
		self.assertEqual(test._raw, "//div")
		self.assertEqual(test._name, "test_name")
		self.assertEqual(test._children[0]._raw, "//a")
		self.assertEqual(test._children[1]._raw, "//b")
		self.assertEqual(test._children[1]._raw, "//b")
		self.assertTrue(test._text)
		self.assertDictEqual(test._attrib, {"test_attrib_key":"test_attrib"})
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
		basic = Instruction("//p", "test",text=True)
		returned, success = basic(self.basic_html)
		self.assertTrue(success)
		self.assertDictEqual(returned,{"test":"Test Basic"})

	def test_no_results(self):
		# TESTING NO RESULTS
		nothing = Instruction("//div[@class='blah']","nothing")
		returned,success = nothing(self.basic_html)
		self.assertIsNone(returned)
		self.assertFalse(success)

	def test_child(self):
		# TESTING CHILD
		parent_a = Instruction("//div[@class='intro']","parent",text=True)
		child_a = Instruction("./h1", "child", text=True)
		parent_a.addChild(child_a)
		rslt_a, success_a = parent_a(self.basic_html)
		self.assertTrue(success_a)
		self.assertDictEqual(rslt_a,{'parent': 'Parent', 'child': 'Child'})

	def test_child_no_result(self):
		# TESTING CHILD NO RESULT
		parent_b = Instruction("//div[@class='intro']","parent",text=True)
		child_b = Instruction("./p", "child", text=True)
		parent_b.addChild(child_b)
		rslt_b, success_b = parent_b(self.basic_html)
		self.assertTrue(success_b)
		self.assertDictEqual(rslt_b, {'parent': 'Parent'})

	def test_multi_element(self):
		# TESTING MULTI ELEMENT
		multi = Instruction("//div[@class='outro']","multi",text=True)
		rslt_m, success_m = multi(self.basic_html)
		self.assertTrue(success_m)
		for i in range(len(rslt_m)):
			self.assertDictEqual(rslt_m[i],{'multi': 'Multi Number '+str(i+1)})

	def test_attributes(self):
		# TESTING ATTRIBUTES
		attrib = Instruction("//a","attrib",attrib={'link':'href'})
		rslt_c, success_c = attrib(self.basic_html)
		self.assertTrue(success_c)
		self.assertDictEqual(rslt_c,{'link': 'www.reddit.com'})

	def test_child_multi(self):
		# TESTING MULTI CHILDREN
		a = Instruction("//div[@class='outro']","parent", text=True)
		b = Instruction("./h1[@class='child_multi']","child",text=True)
		a.addChild(b)
		rslt, worked = a(self.basic_html)
		self.assertTrue(worked)
		self.assertEqual(type(rslt),list)
		self.assertDictEqual(rslt[0],{'parent': 'Multi Number 1', 'child': 'Child Number 1'})
		self.assertDictEqual(rslt[1],{'parent': 'Multi Number 2', 'child': 'Child Number 2'})

