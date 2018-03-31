import os
import sys

if r'\examples' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.scraper import Scraper
from src.instructions import generate_instruction_dict


if __name__ == "__main__":
    # Example main using scraper
    s = Scraper(cores=4,debug=True)
    import ast
    links = [{'url': 'https://www.ebay.com/v/allcategories',
              'headers': {}, 'dictKey': 'categories', "instructionSet":"getCategories"}]

    # Using the function to generate the instruction dictionary
    sub_section_l2 = generate_instruction_dict(".//li[@class='sub-category']/a[@class='categories-with-links']", "l2_subsection", text=True,
                                               etree_text=True,attrib={"link":"href"})
    sub_section_l1 = generate_instruction_dict(".//div[@class='l1-name-wrapper']/a[@class='l1-name categories-with-links']/h3", "l1_subsection",text=True)

    sections = generate_instruction_dict("//div[@class='category-section']", "section", children=[sub_section_l1,sub_section_l2],attrib={'section':
                                                                                                                                             'data-id'})

    instructions = [sections]

    # Running the scraper
    s.addInstructions(instructions,"getCategories")
    s.run(links)
