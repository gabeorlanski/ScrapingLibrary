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

# measurments_regex_short = re.compile(r'([0-9?\.?\-]+)\s?((?![(pcs)(pc)(pairs)(x)])[a-z\"\']{1,3}(?![a-z]))')
clean_html_regex = re.compile(r"(?<=<\/li>)\s+(<\/li>\s+<\/ul>)")
clean_istr = Instruction("//div[@id='ResultSetItems']", "cleaned_results", backup_xpaths=["//ul[@id='ListViewInner']"], return_html=True)

def clean_html(data):
    from time import time
    start = time()
    fixed = clean_html_regex.sub("</ul>", data)
    end = time()
    test = clean_istr(fixed)[1]
    print("Cleaning html took: " + str(end - start))
    return fixed


if __name__ == "__main__":
    s = Scraper(cores=1, debug=True)
    links = {"url":"https://www.ebay.com/sch/i.html?_from=R40&_nkw=&_sacat=180966&_ipg=25", "dictKey":"door_lock_images", "instructionSet": "getImages", "headers": {}}
    getImage = Instruction("./div[contains(@class,'lvpic')]/*/img","image",attrib={'img': 'src'},debug=True,backup_xpaths=["./div[@class='s-item__wrapper clearfix']/div[@class='s-item__image-section']/div[@class='s-item__image']/a/*/img[@class='s-item__image-img']"])
    getList = Instruction("//div[@class='s-item__wrapper clearfix']","listing",attrib={'link': 'href'},children=[getImage])
    getItems = Instruction("//li[contains(@class,'sresult')]","items",children=[getImage],backup_xpaths=["//ul[@class='srp-results srp-list clearfix']/li[contains(@class,'item')]"],debug=True)
    s.addInstructions([getItems], "getImages")
    # s.run(links+links_2+links_3)
    s.run([links])
