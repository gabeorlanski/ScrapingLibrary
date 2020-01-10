import json
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
from ebaysdk.shopping import Connection as Shopping
shopping = Shopping(appid='GabrielO-Flipper-PRD-6246ab075-45501e29', config_file='ebay.yaml')
import json
import os
x = json.loads(open("test_data.json").read())
print("Imported test_data.json")
q = {}
items = {}
items_by_search = defaultdict(dict)
titles_by_search = defaultdict(list)
titles = []
long_titles = []

print("Iterating over keys...")
for k in list(x.keys()):
    print(list(x[k].keys()))
    print(k)
    y = x[k]["listings"]
    search = k.split("_pg")[0]
    
    for i in y.keys():
        children = y[i]["children"][0]
        title = ""
        link = ""
        price = 0
        measurements = {}
        quantity = {}
        pid = []
        for c in children.keys():
            if "title" in c:
                title = children[c]["title"]
                title = title.replace("\n","").replace("\t","")
                if "new listing" in title.lower():
                    title = " ".join(title.split()[2:])
                    
                tmp_measure = {}
                for m in children[c]["measurements"].keys():
                    tmp_measure[m] = list(set(children[c]["measurements"][m]))
                measurements =tmp_measure
                title_short = children[c]["title_shortened"]
                quan_tmp = defaultdict(list)
                for quan in children[c]["quantity"].keys():
                    quan_tmp[quan].append(children[c]["quantity"][quan])
                        
                quantity = dict(quan_tmp)
                pid = children[c]["product_ids"]
            elif "url" in c:
                link = children[c]["link"]
            else:
                price = children[c]["price"]
        e_id = link.split(r"/")[-1].split("?")[0]
        if title != "ELEM_MEMBER_TEXT_NONE" and title != "new listing":
            long_titles.append(title)
            titles.append(title_short)
            items["item_"+str(e_id)] = {"quantity":quantity,"measurements":measurements,"price":price,"title_short":title_short,"title":title,"link":link,"eid":e_id,"pid":pid}
            items_by_search[search]["item_"+str(e_id)] = items["item_"+str(e_id)]
            titles_by_search[search].append(title)
print("Done iterating over keys")

import datetime
current_date = datetime.date.today().strftime("%B %d %Y")
print("Todays date is: "+current_date)
path_to_date = os.path.join(os.getcwd()+r"\data", current_date)
if not os.path.isdir(path_to_date):
    os.mkdir(path_to_date)
items_by_search = dict(items_by_search)
current_time = datetime.datetime.now().strftime("%I%p")
for i in items_by_search.keys():
    with open(path_to_date+"\\"+i+".json","w", encoding='utf-8') as f:
        f.write(json.dumps(items_by_search[i], indent=4, sort_keys=True))
    with open(os.getcwd() + r"\parsed_data"+"\\"+i+".json","w", encoding='utf-8') as f:
        f.write(json.dumps(items_by_search[i], indent=4, sort_keys=True))
    with open(os.getcwd() + r"\parsed_data"+"\\"+i+".txt","w", encoding='utf-8') as f:
        for t in titles_by_search[i]:
            f.write(t.strip()+"\n")
print("Finished")