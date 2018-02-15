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
basic_html = open(os.getcwd() + r'\tests\instruction_test_html\basic_call.html').read()


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
    _debug = False
    _numresults = 0
    _backups = None
    _backupsraw = None
    parser = None
    context = None

    def __init__(self, path, name=None, children=None, text=False, attrib=None, get_data=False, key=None, debug=False, backup_xpaths=[]):
        """
        :param path: The XPATH as a string
        :type path: str
        :param name: The name of this instruction
        :type name: str
        :param children: List of instructions to be executed on the result of this command
        :type children: [Instruction]
        :param text: If you need to get the text of the result of the xpath
        :type text: bool
        :param attrib: Dictionary of all the attributes from the result that you want to get
        :type attrib: {name:attribute}
        :param get_data: If this Instruction has data you want to get
        :type get_data: bool
        :param key: the key that the parent will see this instruction as
        :type key: Whatever data type you want to use as an id
        :param debug: Enable Debugging
        :type debug: bool
        :param backup_xpaths: Any backup xpath to get the same data to deal with any changes in the html from page to page
        :type backup_xpaths: [str]
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
        self._debug = debug
        if len(backup_xpaths) != 0:
            self._backupsraw = backup_xpaths
            self._backups = []
            for i in self._backupsraw:
                self._backups.append(etree.XPath(i))

    def debug_print(self):
        """

        :rtype: None
        """
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

    def _retrieveData(self, elem):

        rtr_dict = dict()
        if self._text:
            rtr_dict[self._name] = elem.text.strip()
        for a in self._attrib.keys():
            rtr_dict[a] = elem.attrib[self._attrib[a]]
        c_data = []
        for c in self._children:
            success = c(elem)
            a = c.data()

            if success:
                c_data.append(a)
        try:
            rtr_dict["num_children"] = len(self._children)
        except:
            rtr_dict["num_children"] = 0
        rtr_dict["children"] = c_data
        return rtr_dict

    def __call__(self, context):
        if type(context) == str:
            parser = etree.HTMLParser(encoding="utf-8")
            context_use = etree.parse(StringIO(context), parser=parser)
        else:
            context_use = context

        # Get the results from the xpath
        result = self._xpath(context_use)
        self._numresults = len(result)

        # Debugging stuff
        if self._debug:
            print("".join("-"))
            print("NAME: " + self._name)

        # If there are no results, try backups. If that fails, return false
        if len(result) == 0:
            if not self._backups:
                return False

            # Iterate through backups until either a result is found, or  it reaches the end
            backup_iter = iter(self._backups)
            while len(result) == 0:
                try:
                    backup = next(backup_iter)
                except:
                    return False

                result = backup(context_use)
            if len(result) == 0:
                return False

        if self._debug:
            for i in result:
                print(etree.tostring(i, pretty_print=True, method='xml').decode('utf-8').strip())
                print(basic_html.find(etree.tostring(i, pretty_print=True, method='xml').decode('utf-8').strip()))

        data = {}
        if len(result) == 1:
            result_single = result[0]
            data["result_1"] = self._retrieveData(result_single)
            self._data = data
            return True

        # Create a dict of the results
        # TODO: Switch this from list format to a dict format

        for i, j in zip(result, range(len(result))):
            info_dict = self._retrieveData(i)
            data["result_" + str(j + 1)] = info_dict

        self._data = data
        return True

    def key(self):
        return self._key

    def data(self, minimal=True):
        if minimal:
            return self._data

        return dict(num_results=self._numresults, xpath=self._raw, name=self._name, data=self._data)

    def get_format(self, minimal=True):
        """
        :return: A mock-up of what the actual format would look like
        :rtype: dict
        """
        rtr = dict(num_results=0, xpath=self._raw, name=self._name, data={})
        result_data = {}
        if self._attrib:
            for i in self._attrib.keys():
                result_data[i] = "Data from: " + self._attrib[i]
        if self._text:
            result_data[self._name] = "Text data"

        if self._children:
            result_data["num_children"] = len(self._children)
            c_data = []
            for c in self._children:
                child_dct = c.get_format()
                c_data.append(child_dct)

            result_data["children"] = c_data

        rtr['data']['result_1'] = result_data
        if minimal:
            return dict(result_1=result_data)
        return rtr


