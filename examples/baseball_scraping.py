import os
import sys

if r'\examples' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.scraper import Scraper
from src.instructions import *
from src.regex_functions import *
import string
from nltk.corpus import stopwords


if __name__ == "__main__":
    # Example main using scraper
    s = Scraper(cores=1, debug=True)

    links = [{
                "url"    :"https://www.baseball-reference.com/boxes/ARI/ARI201704020.shtml", "instructionSet": "getPlayerStats",
                "headers": {},"dictKey":"playerStats"
        }]

    getTable = Instruction("//div[@class='media-item logo']", "playerTable",return_html=True, debug=True)


    # Running the scraper
    s.addInstructions([getTable], "getPlayerStats")
    # s.run(links+links_2+links_3)
    s.run(links)
