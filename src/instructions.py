from lxml import etree
from io import StringIO
import os
import sys
if r'\src' in os.getcwd():
	sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
	os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))
"""
Wrapper for xpath commands that allows the user to easily use xpaths
"""
basic_html = open(os.getcwd()+r'\tests\instruction_test_html\basic_call.html').read()
class Instruction:
	# NEVER MODIFY THESE VARIABLES OUTSIDE OF MEMBER FUNCTIONS!
	_name = None
	_raw = None
	_xpath = None
	_children = []
	_text = False
	_attrib = None
	_getdata = False
	_id = None
	_data = None

	parser = None
	context = None

	def __init__(self, path, name=None, children=None, text=False, attrib=None, get_data=False, key=None):
		"""
		:param path: The XPATH as a string
		:type path: str
		:param name: The name of this instruction
		:type name: str
		:param children: List of instructions to be executed on the result of this command
		:type children: [Instruction]
		:param text: If you need to get the text of the result of the xpath
		:type text: bool
		:param attrib: List of all the attributes from the result that you want to get
		:type attrib: [{name:attribute}]
		:param get_data: If this Instruction has data you want to get
		:type get_data: bool
		:param key: the key that the parent will see this instruction as
		:type key: Whatever data type you want to use as an id
		"""
		self._raw = path
		self._xpath = etree.XPath(self._raw)
		self._name = name
		if children is not None:
			self._children = children
		else:
			self._children = []
		self._text = text
		if attrib is not None:
			self._attrib = attrib
		else:
			self._attrib = {}

		self._getdata = get_data
		self._key = key

	def _debug(self):
		print("-- DEBUGGING --")
		print("NAME: " + self._name)
		print("XPATH: " + self._raw)
		print("len(_CHILDREN): " + str(len(self._children)))

	def addChild(self, i):
		# TODO: add in checking for duplicate instructions
		if type(i) != Instruction:
			raise TypeError("Expected i to by type 'Instruction', instead got: " + str(type(i)))
		self._children.append(i)

	def getName(self):
		return self._name

	def _retrieveData(self,elem):
		# TODO: switch this to return a key if need be
		rtr_dict = dict()
		if self._text:
			rtr_dict[self._name] = elem.text.strip()
		for a in self._attrib.keys():
			rtr_dict[a] = elem.attrib[self._attrib[a]]
		for c in self._children:
			success = c(elem)
			a = c.data()
			if success:
				rtr_dict = {**rtr_dict, **a}
		return rtr_dict

	def __call__(self, context):
		context_use = None
		if type(context) == str:
			parser = etree.HTMLParser(encoding="utf-8")
			context_use = etree.parse(StringIO(context), parser=parser)
		else:
			context_use = context

		result = self._xpath(context_use)
		print("".join("-"))
		print("NAME: " + self._name)
		for i in result:
			if type(context) == str:
				original = context
			else:
				original = ""
			print(etree.tostring(i, pretty_print=True, method='xml').decode('utf-8').strip())
			print(basic_html.find(etree.tostring(i, pretty_print=True, method='xml').decode('utf-8').strip()))
		# If there is no results, return false
		if len(result) == 0:
			return False

		if len(result) == 1:
			result_single = result[0]
			rtr_dict = self._retrieveData(result_single)
			self._data = rtr_dict
			return True

		# Create a dict of the results
		# TODO: Switch this from list format to a dict format
		answer = {}
		for i, j in zip(result, range(len(result))):
			info_dict = self._retrieveData(i)
			answer[self._name+"_"+str(j)] = info_dict

		self._data = answer
		return True

	def key(self):
		return self._key

	def data(self):
		return self._data


if __name__ == '__main__':
	basic_html = open(os.getcwd() + r'\tests\instruction_test_html\basic_call.html').read()
	# TESTING MULTI CHILDREN
	a = Instruction("//div[@class='outro']", "parent", text=True)
	b = Instruction("./h1[@class='child_multi']", "child", text=True)
	a.addChild(b)
	worked = a(basic_html)
	rslt = a.data()
	print(rslt)
