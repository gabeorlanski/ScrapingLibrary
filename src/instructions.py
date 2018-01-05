from lxml import etree
from io import StringIO
"""
#Wrapper for xpath commands that allows the user to easily use xpaths
"""


class Instruction:
	# NEVER MODIFY THESE VARIABLES OUTSIDE OF MEMBER FUNCTIONS!
	_name = None
	_raw = None
	_xpath = None
	_children = []
	_text = False
	_attrib = None
	_getdata = False

	parser = None
	context = None

	def __init__(self, path, name=None, children=None, text=False, attrib=None, get_data=False):
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
		rtr_dict = dict()
		if self._text:
			rtr_dict[self._name] = elem.text.strip()
		for a in self._attrib.keys():
			rtr_dict[a] = elem.attrib[self._attrib[a]]
		for c in self._children:
			a, success = c(elem)
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

		# If there is no results, return false
		if len(result) == 0:
			return None, False

		if len(result) == 1:
			result_single = result[0]
			rtr_dict = self._retrieveData(result_single)
			return rtr_dict, True

		answer = [None for i in result]
		for i, j in zip(result, range(len(result))):
			info_dict = self._retrieveData(i)
			answer[j] = info_dict

			# for c in self._children:
		return answer, True






