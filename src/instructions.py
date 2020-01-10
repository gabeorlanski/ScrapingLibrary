import os
import sys
from io import StringIO

from lxml import etree

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
    _optionsdict = {}
    _etree = False
    _apply = None
    parser = etree.HTMLParser(encoding="utf-8")
    context = None
    _cur_key = None

    def __init__(self, xpath, name=None, children=None, text=False, attrib=None, get_data=False, key=None, debug=False, backup_xpaths=[], etree_text=False, apply_function=None, run_backups=False,return_html=False):
        """
        :param xpath: The XPATH as a string
        :type xpath: str
        :param name: The name of this instruction
        :type name: str
        :param children: Either a List of getListings, or a list of dicts that have keys: name, xpath(path), children(list of these dictionaries),options(all of the arguments for __init__ that are not explicit keys of this dictionary)
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
        :param etree_text: the parameter text must also be True, uses the etree.tostring() functionality from lxml
        :type etree_text: bool
        :param apply_function: user function that will process results
        :type apply_function: function that returns the modified data dict, MUST take one argument and that will be the results dictionary of data
        from the
        xpath
        :param run_backups: If you want to run the backups all of the type
        :type run_backups: bool
        """
        self._run_backups = False
        self._raw = xpath
        self._xpath = etree.XPath(self._raw)
        self._name = name
        tmp_children = []
        if children is not None and len(children) != 0:
            if type(children[0]) == dict:
                for i in children:
                    child = self.create_another(i)
                    tmp_children.append(child)
                self._children = tmp_children
            else:
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
        self._etree = etree_text
        self._apply = apply_function
        self._run_backups = run_backups
        self._return_html = return_html
        if len(backup_xpaths) != 0:
            self._backupsraw = backup_xpaths
            self._backups = []
            for i in self._backupsraw:

                self._backups.append(etree.XPath(i))

        # Options dict handling
        opts = dict()

        if text:
            opts["text"] = text

        if attrib is not None:
            opts['attrib'] = attrib

        if get_data:
            opts['get_data'] = get_data

        if key is not None:
            opts['key'] = key

        if debug:
            opts['debug'] = debug

        if len(backup_xpaths) != 0:
            opts['backup_xpaths'] = backup_xpaths
        if etree_text:
            opts['etree_text'] = etree_text

        if apply_function:
            opts['apply_function'] = apply_function
        if run_backups:
            opts['run_backups'] = run_backups
        if return_html:
            opts['return_html'] = True
        self._optionsdict = opts

    def debug_print(self):
        """

        :rtype: None
        """
        print("-- DEBUGGING --")
        print("NAME: " + self._name)
        print("XPATH: " + self._raw)
        print("len(_CHILDREN): " + str(len(self._children)))

    def addChild(self, i):
        # TODO: add in checking for duplicate getListings
        if type(i) != Instruction:
            raise TypeError("Expected i to by type 'Instruction', instead got: " + str(type(i)))
        self._children.append(i)

    def getName(self):
        return self._name

    def _retrieveData(self, elem,key=None):

        rtr_dict = dict()
        if self._text:
            if self._debug:
                print("Getting text for instruction {} ...".format(self._name))
            try:
                if self._etree:
                    rtr_dict[self._name] = etree.tostring(elem, method="text").decode().strip()
                else:
                    rtr_dict[self._name] = elem.text.strip()
            except:
                try:
                    rtr_dict[self._name] = elem.text.strip()
                except Exception as e:
                    if self._debug:
                        print("ERROR with getting text for instruction {}! Exception raised: {}".format(self._name,e))
                    rtr_dict[self._name] = "ELEM_MEMBER_TEXT_NONE"
        if self._debug:
            print(self._name + " getting attrib")
        for a in self._attrib.keys():
            try:
                rtr_dict[a] = elem.attrib[self._attrib[a]]
            except Exception as e:
                if self._debug:
                    print("ERROR with getting attrib {}:{} for instruction {}!".format(a, self._attrib[a], self._name))
        children_results = {}
        if self._return_html:
            rtr_dict["html"] = etree.tostring(elem)
        for c in self._children:
            success, a = c(elem,key)

            if success:
                new_a = {}
                for k in a.keys():
                    new_a[k.replace("result", c._name)] = a[k]
                children_results = {**children_results, **new_a}
        try:
            rtr_dict["num_children"] = len(self._children)
        except:
            rtr_dict["num_children"] = 0
        if children_results:
            rtr_dict["children"] = [children_results]
        else:
            rtr_dict["children"] = []

        if self._apply:
            rtr_dict = self._apply(rtr_dict)
        return rtr_dict

    def __call__(self, c_text,key=None):
        if self._debug:
            print("-" * 10)
            print(self._raw + " called on context")
            print(key)
        if type(c_text) == str:
            context_use = etree.parse(StringIO(c_text), parser=self.parser)
        else:
            context_use = c_text

        # Get the results from the xpath
        try:
            result = self._xpath(context_use)
        except Exception as e:
            result = 0
            if self._debug:
                print("ERROR WITH XPATH. Exception is: '{}'".format(str(e)))
            pass

        # Debugging stuff
        if self._debug:
            print("NAME: " + self._name)

        # If there are no results, try backups. If that fails, return false
        if len(result) == 0:
            if self._debug:
                print("No Results found for Instruction: {}".format(self._raw))
            if not self._backups:
                if self._debug:
                    print("No Backups in instruction {}...".format(self._name))
                    print("-" * 10)
                return False, None

            # Iterate through backups until either a result is found, or  it reaches the end
            backup_iter = 0
            backup = None
            while len(result) == 0:
                try:
                    backup = self._backups[backup_iter]
                except:
                    if self._debug:
                        print("No Results found for Instruction {} after running backup...".format(self._name))
                        print("-" * 10)
                    return False, None

                result = backup(context_use)
                backup_iter += 1

            if self._debug:
                print("Results found for Instruction {} after running backup...".format(self._name))

        # If run backups option is enabled, run those as well
        if self._run_backups:
            for backup in self._backups:
                result = result + backup(context_use)
        if self._debug:
            print("{} found {} results".format(self._name, len(result)))

        data = {}
        if len(result) == 1:
            import copy
            result_single = result[0]
            data["result_1"] = self._retrieveData(copy.deepcopy(result_single),key)
            if self._debug:
                print("-" * 10)
            return True, data

        # Create a dict of the results
        for i, j in zip(result, range(len(result))):
            import copy
            info_dict = self._retrieveData(copy.deepcopy(i),key)
            data["result_" + str(j + 1)] = info_dict
        if self._debug:
            print("-" * 10)
        return True, data

    def key(self):
        return self._key

    # def data(self, minimal=True):
    #     if minimal:
    #         return self._data
    #
    #     return dict(num_results=_numresults, xpath=self._raw, name=self._name, data=self._data)

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

    def __eq__(self, other):
        if self._name != other._name:
            return False

        if self._raw != other._raw:
            return False

        if self._children != other._children:
            return False

        if self._text != other._text:
            return False

        if self._attrib != other._attrib:
            return False

        if self._id != other._id:
            return False

        if self._backups != other._backups:
            return False

        if self._getdata != other._getdata:
            return False

        return True

    def __ne__(self, other):
        if self == other:
            return False
        return True

    def get_init_dict(self, text=False):
        rtr = {"name": self._name, "xpath": self._raw, "children": []}
        if text:
            rtr["children"] = {}
        for c in self._children:
            if text:
                rtr["children"][c.getName()] = c.get_init_dict(text)
            else:
                rtr['children'].append(c.get_init_dict())

        rtr = {**rtr, **self._optionsdict}

        if text and "apply_function" in rtr:
            rtr["apply_function"] = rtr["apply_function"].__name__
        return rtr

    def create_another(self, d):
        return type(self)(**d)

    def debug(self):
        return self._debug

    def set_key(self, key):
        self._cur_key = key


def generate_instruction_dict(xpath, name=None, children=None, text=False, attrib=None, get_data=False, key=None, debug=False, backup_xpaths=[], etree_text=False, apply_function=None,
                              run_backups=False, return_html=False):
    opts = dict()

    if text:
        opts["text"] = text

    if attrib is not None:
        opts['attrib'] = attrib

    if get_data:
        opts['get_data'] = get_data

    if key is not None:
        opts['key'] = key

    if debug:
        opts['debug'] = debug

    if len(backup_xpaths) != 0:
        opts['backup_xpaths'] = backup_xpaths
    if etree_text:
        opts['etree_text'] = True
    if apply_function:
        opts["apply_function"] = apply_function

    if run_backups:
        opts['run_backups'] = run_backups
    if return_html:
        opts['return_html'] = True
    rtr = {"name": name, "xpath": xpath, "children": []}
    if children:
        for c in children:
            rtr['children'].append(c)

    rtr = {**rtr, **opts}

    return rtr
