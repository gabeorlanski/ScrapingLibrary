import os
import sys

if r'\examples' in os.getcwd():
    sys.path.insert(0, os.path.normpath(os.getcwd() + os.sep + os.pardir))
    os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))

from src.scraper import Scraper
from src.instructions import generate_instruction_dict


def ex_apply_function(data):
    # Example apply function
    price = data["price"]
    price = price.replace('\t', "").replace("\n", "")
    price = price.split(" to ")[0].replace("$", "")
    price = price.split("Trending")[0].replace("$", "")
    try:
        data["price"] = float(price)
    except:
        data["price"] = float(price.replace(",", ""))
    return data


if __name__ == "__main__":
    # Example main using scraper
    s = Scraper(cores=4, debug=True)
    import ast

    links = [{
                 'url'    : 'https://www.ebay.com/sch/i.html?_odkw=superlunary&_osacat=0&_ipg=200&_from=R40&_trksid=m570.l1313&_nkw=superlunary&_sacat=0',
                 'headers': {}, 'dictKey': 'superlunary_test', "instructionSet":"getListings"
             },
             {
                 'url'    : 'https://www.ebay.com/sch/i.html?_odkw=blank&_osacat=0&_ipg=200&_from=R40&_trksid=m570.l1313&_nkw=blank&_sacat=0',
                 'headers': {}, 'dictKey': 'blank_test', "instructionSet":"getListings"
             },
             {
                 'url'    : 'https://www.ebay.com/sch/i.html?_odkw=starve&_osacat=0&_ipg=200&_from=R40&_trksid=m570.l1313&_nkw=starve&_sacat=0',
                 'headers': {}, 'dictKey': 'starve_test', "instructionSet":"getListings"
             }]

    # Using the function to generate the instruction dictionary
    listing_title = generate_instruction_dict("./h3[@class='lvtitle']/a", "title", text=True)
    listing_price = generate_instruction_dict("./ul[@class='lvprices left space-zero']/li[@class='lvprice prc']/span[@class='bold']", "price",
                                              text=True, apply_function=ex_apply_function)  # passing the apply function to the generator
    listings = generate_instruction_dict("//li[@class='sresult lvresult clearfix li shic']", "listings", children=[listing_title, listing_price], backup_xpaths=["//li[@class='sresult lvresult clearfix li']"], run_backups=True)

    instructions = [listings]

    # Running the scraper
    s.addInstructions(instructions,"getListings")
    s.run(links)
