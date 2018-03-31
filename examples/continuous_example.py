import os
import sys
import urllib
from urllib.parse import urlparse, parse_qs
if r'\examples' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.scraper import Scraper
from src.instructions import generate_instruction_dict


def ex_function(key,data, instruction_set):
    # Example apply function
    url = data["link"]
    total = int(data["results"]["result_1"]["results"].split("results")[0].strip())
    #q = parse_qs(urlparse(url).query)
    num_results = data["listings"]["num_results"]
    total_pages = total // num_results
    rtr = []
    for i in range(2,total_pages+1):
        rtr.append({"dictKey":key,"url":url+"&_pgn={}".format(i), "headers":{},"instructionSet":"getListings"})
    return [key,data,instruction_set],rtr


if __name__ == "__main__":
    # Example main using scraper
    s = Scraper(cores=2,debug=True,continuous_adding=True)
    links = [{
                 'url'    : 'https://www.ebay.com/sch/i.html?_odkw=superlunary&_osacat=0&_ipg=200&_from=R40&_trksid=m570.l1313&_nkw=superlunary&_sacat=0',
                 'headers': {}, 'dictKey': 'superlunary_test', "instructionSet":"getListings"
             }
        ]
    rules = {"getListings":{"apply":ex_function,"keyApply":"_depth"}}
    stop_cond = {"dictKey":"superlunary_test"}
    s.continuous_params(rules,stop_cond)
    listing_title = generate_instruction_dict(".//h3[@class='lvtitle']/a", "title", text=True)
    listings = generate_instruction_dict("//li[@class='sresult lvresult clearfix li shic']", "listings", children=[listing_title],backup_xpaths=["//li[@class='sresult lvresult clearfix li']"], run_backups=True)
    total_results = generate_instruction_dict("//h1[@class='rsHdr']", "results",text=True)
    instructions =[listings,total_results]

    s.addInstructions(instructions, "getListings")
    s.run(links)