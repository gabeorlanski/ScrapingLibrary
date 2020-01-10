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


test_files = ['business_lights_test.txt', 'crystal_oscilators_test.txt', 'headphones_test.txt', 'lcd_rpi.txt', 'networking_test.txt', 'port_radio_test.txt']
# test_files = ["3mm_ir_test.txt"]
punct = set(string.punctuation)
punct.remove("-")
punct.remove("/")
punct.remove(".")
punct = list(punct)


def ex_apply_function(data):
    # Example apply function
    if type(data["price"]) is not list:
        data["price"] = [data["price"]]
    tmp = []
    for i in data["price"]:
        price = i.strip()
        price = price.replace('\t', "").replace("\n", "")
        price = price.split(" to ")[0].replace("$", "")
        price = price.split("Trending")[0].replace("$", "")
        try:
            tmp.append(float(price))
        except:
            try:
                tmp.append(float(price.replace(",", "")))
            except:
                pass
    data["price"] = tmp
    return data


clean_istr = Instruction("//div[@id='ResultSetItems']", "cleaned_results", backup_xpaths=["//ul[@id='ListViewInner']"], return_html=True)
clean_html_regex = re.compile(r"(?<=<\/li>)\s+(<\/li>\s+<\/ul>)")


def clean_html(data):
    from time import time
    start = time()
    fixed = clean_html_regex.sub("</ul>", data)
    end = time()
    test = clean_istr(fixed)[1]
    print("Cleaning html took: " + str(end - start))
    return fixed


def create_multi_pages(url, pages, key):
    rtr = []
    if "_pgn=" in url:
        url, tmp = url.split("_pgn=")
        try:
            current_page = int(tmp)
        except:
            tmp = tmp.split("&")[0]
            current_page = int(tmp)
    else:
        current_page = 1
    if pages == 1:
        pages = 2
        current_page = 0
    for i in range(current_page, current_page + pages-1 ):
        # if i > 35:
        rtr.append({
                "url"    : url + "&_pgn=" + str(i) + "&_skc=" + str((i-1) * 200), "dictKey": key + "_pg" + str(i), "instructionSet": "getListings",
                "headers": {}
        })
        # else:
        #     rtr.append({
        #     "url": url + "&_pgn=" + str(i), "dictKey": key + "_pg" + str(i), "instructionSet": "getListings", "headers": {}
        #     })

    return rtr


def info_from_title(data):
    date = date_regex.findall(data["title"])
    try:
        data["sold_on"] = date[0]
    except:
        data["sold_on"] = ""
    data["title"] = date_regex.sub(" ", data["title"]).strip()
    title_shortened = data["title"].lower()

    title_shortened, data["dimensions"] = get_dimensions(title_shortened)

    title_shortened, data["measurements"] = get_measurements_range(title_shortened)
    title_shortened, tmp_measure = get_measurements(title_shortened)
    if data["measurements"] and tmp_measure:
        for i in tmp_measure.keys():
            if i in data["measurements"]:
                cur_measurements = set(data["measurements"][i])
                for m in tmp_measure[i]:
                    cur_measurements.add(m)
                data["measurements"][i] = list(cur_measurements)
            else:
                data["measurements"][i] = tmp_measure[i]
    else:
        if tmp_measure:
            data["measurements"] = tmp_measure

    title_shortened, data["quantity"] = get_quantity(title_shortened)
    for word in title_shortened.split():
        if word in list(stopwords.words('english')) or word in list(string.punctuation) + ["-", "&"]:
            title_shortened.replace(word, "")
    # title_shortened = pairs_regex.sub(title_shortened," ")
    title_shortened = ''.join(ch for ch in title_shortened if ch not in punct)
    ranges_results = possible_ranges.findall(title_shortened)
    for first, second in ranges_results:
        if "-" not in first or "-" not in second:
            first_str, first_result = run_all(first)
            title_shortened = title_shortened.replace(first + "-" + second, first + " - " + second)
            if first_str != first:

                for k in first_result.keys():
                    if first_result[k]:
                        if k == "measurements":
                            for m in first_result[k].keys():
                                if m not in data["measurements"]:
                                    data["measurements"][m] = first_result[k][m]
                                else:
                                    cur = set(data["measurements"][m])
                                    for measure in first_result[k][m]:
                                        cur.add(measure)
                                    data["measurements"][m] = list(cur)
                        elif k == "quantity":
                            for q in first_result[k].keys():
                                if q in data["quantity"]:
                                    data["quantity"][q] = max(data["quantity"][q], first_result[k][q])
                                else:
                                    data["quantity"][q] = first_result[k][q]
                title_shortened = title_shortened.replace(first, " ")

            second_str, second_result = run_all(second)
            if second_str != second:

                for k in second_result.keys():
                    if second_result[k]:
                        if k == "measurements":
                            for m in second_result[k].keys():
                                if m not in data["measurements"]:
                                    data["measurements"][m] = second_result[k][m]
                                else:
                                    cur = set(data["measurements"][m])
                                    for measure in second_result[k][m]:
                                        cur.add(measure)
                                    data["measurements"][m] = list(cur)
                        elif k == "quantity":
                            for q in second_result[k].keys():
                                if q in data["quantity"]:
                                    data["quantity"][q] = max(data["quantity"][q], second_result[k][q])
                                else:
                                    data["quantity"][q] = second_result[k][q]
                title_shortened = title_shortened.replace(second, " ")
    data["product_ids"] = list(set(product_num.findall(title_shortened)))
    data["title_shortened"] = " ".join(title_shortened.split())

    return data


if __name__ == "__main__":
    # Example main using scraper
    s = Scraper(cores=6, debug=True, apply_functions=[clean_html])

    # links = create_multi_pages("https://www.ebay.com/sch/i.html?_from=R40&_nkw=melamine+sponge&_sacat=0&_ipg=200", 1, "melamine_foam") + create_multi_pages("https://www.ebay.com/sch/i.html?_from=R40&_nkw=ddr4+16gb&_sacat=0&LH_TitleDesc=0&LH_TitleDesc=0&_ipg=200", 1, "ddr4_16gb") + create_multi_pages("https://www.ebay.com/sch/i.html?_from=R40&_nkw=yeezy&_sacat=0&LH_TitleDesc=0&LH_TitleDesc=0&_dmd=1&rt=nc&_ipg=200", 1, "yeezy")
    links = [{
        "url": "https://www.ebay.com/sch/i.html?_from=R40&_nkw=melamine+foam&_sacat=0&LH_TitleDesc=0&_blrs=spell_check&LH_TitleDesc=0&_ipg=200", "dictKey": "melamine_foam", "instructionSet": "getListings", "headers": {}
    }, {
        "url": "https://www.ebay.com/sch/i.html?_from=R40&_nkw=ddr4+16gb&_sacat=0&LH_TitleDesc=0&LH_TitleDesc=0&_ipg=200", "dictKey": "ddr4_16gb", "instructionSet": "getListings", "headers": {}
    }, {
        "url": "https://www.ebay.com/sch/i.html?_from=R40&_nkw=yeezy&_sacat=0&LH_TitleDesc=0&LH_TitleDesc=0&_dmd=1&rt=nc&_ipg=200", "dictKey": "yeezy","instructionSet": "getListings", "headers": {}
    }
    ]
    # links_2 = create_multi_pages(
    #         "https://www.ebay.com/sch/i.html?_from=R40&_trksid=m570.l1313&_nkw=&_sacat=45462&_ipg=200",
    #         25,"full_bed_comforter"
    # )
    # links_3 = create_multi_pages(
    #         "https://www.ebay.com/sch/i.html?_from=R40&_trksid=p2499334.m570.l1313.TR0.TRC0.H0.TRS0&_nkw=&_sacat=180966&_ipg=200",
    #         25,"door_locks"
    # )
    # create_multi_pages("https://www.ebay.com/sch/Pushbutton-Switches/58166/i.html?_from=R40&_nkw=Pushbutton+Switches+round&_ipg=200&rt=nc", 1,
    #     "pushbutton_switches_round")
    #     +create_multi_pages(
    # "https://www.ebay.com/sch/Pushbutton-Switches/58166/i.html?_from=R40&_nkw=Pushbutton+Switches+Square&_ipg=200&rt=nc",
    # 5, "pushbutton_switches_square") +create_multi_pages(
    # "https://www.ebay.com/sch/Component-Solenoids/181878/i.html?_from=R40&_nkw=Component+solenoids&_ipg=200&rt=nc",
    # 10, "component_solenoids") +

    # Using the function to generate the instruction dictionary
    listing_sold_date = generate_instruction_dict("./ul[@class='lvdetails left space-zero full-width']/li[@class='timeleft']/span["
                                                  "@class='tme']/span",
                                                  "sold_on",
                                                  text=True,
                                                  backup_xpaths=[
        "./div[@class='s-item__details clearfix']/span[@class='s-item__detail s-item__detail--secondary']/span[@class='s-item__ended-date s-item__endedDate']"])
    listing_exact_sold = generate_instruction_dict("./div[@class='s-item__detail s-item__detail--secondary']/span[@class='s-item__ended-date s-item__endedDate']",
                                                   "exact_sold_on",
                                                   text=True
                                                   )

    listing_link = generate_instruction_dict("./h3[@class='lvtitle']/a", "title", attrib={'link': 'href'}, text=True, apply_function=info_from_title, backup_xpaths=["./a[@class='s-item__link']"],
                                             etree_text=True)

    listing_price = generate_instruction_dict("./ul[contains(@class,'lvprices')]/li[@class='lvprice prc']/span[@class='bold "
                                              "bidsold']/span[@class='sboffer']", "price", text=True, apply_function=ex_apply_function,
                                              backup_xpaths=["./ul[contains(@class,'lvprices')]/li[@class='lvprice prc']/span[@class='bold "
                                                             "bidsold']/span[@class='prRange']", "./ul[contains(@class,'lvprices')]/li[@class='lvprice prc']/span[@class='bold bidsold']",
                                                             "./div[@class='s-item__details clearfix']/div[@class='s-item__detail s-item__detail--primary']/span[@class='s-item__price']/span[@class='POSITIVE']",
                                                             "./div[@class='s-item__details clearfix']/div[@class='s-item__detail s-item__detail--primary']/span[@class='s-item__price']/span[@class='STRIKETHROUGH POSITIVE']"])  # passing the apply
    # function to the generator
    listing_shipping = generate_instruction_dict("./ul[contains(@class,'lvprices')]/li[@class='lvshipping']/span[@class='ship']/span", "shipping", text=True, etree_text=True,
                                                 backup_xpaths=["./div[@class='s-item__details clearfix']/div[@class='s-item__detail s-item__detail--primary']/span[contains(@class,'shipping')]"])

    listing_format = generate_instruction_dict("./ul[contains(@class,'lvprices')]/li[@class='lvformat']/span", "format", text=True, backup_xpaths=[
        "./div[@class='s-item__details clearfix']/div[@class='s-item__detail s-item__detail--secondary']/span[@class='s-item__dynamic s-item__buyItNowOption']"])

    listing_location = generate_instruction_dict("./ul[@class='lvdetails left space-zero full-width']/li[not(@class)]", "location", text=True, backup_xpaths=[
        "./div[@class='s-item__details clearfix']/div[@class='s-item__detail s-item__detail--secondary']/span[@class='s-item__location s-item__itemLocation']"])

    listing_condition = generate_instruction_dict("./div[@class='lvsubtitle']", "condition", text=True, backup_xpaths=["./div[@class='s-item__subtitle']/span[@class='SECONDARY_INFO']"])
    listings = generate_instruction_dict("//li[@class='sresult lvresult clearfix li']", "listings",
                                         children=[listing_link, listing_price, listing_sold_date, listing_shipping, listing_condition, listing_format, listing_location, listing_exact_sold],
                                         backup_xpaths=["//div["
                                                        "@class='s-item__info clearfix']"])

    getDesc = generate_instruction_dict("//div[@class='vi-desc-maincntr']", "descriptions", children=[])

    getListings = [listings]

    # Running the scraper
    s.addInstructions(getListings, "getListings")
    # s.run(links+links_2+links_3)
    s.run(links)
