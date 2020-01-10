import re

measurement_list = ["in(?:ch(?:es?)?)?", "v(?:olts?)?", "a(?:mps?)", "m(?:eter(?:s?)?)?", "feet", "foot", "ft", '"', "'", "j(?:oule(?:s?)?)?",
                    "w(?:att(?:s?)?)?", "vdc", "ma", "mbs", "mhz", "megahertz", "ppm", "uf", "pf", "mm", "vac", "deg", "mfd", "hz", "ml",
                    "ounce(?:s?)?", "oz", "g", "gram"]

measurement_list.sort(key=len, reverse=True)
measurement_dict = {
    "mm"  : "millimeters", "in": "inches", '"': "inches", "'": "feet", "nm": "nanometers", "v": "volts", "w": "watts", "d": "day", "a": "amps",
    "inch": "inches", "hz": "hertz", "j": "joules", "ft": "feet", "foot": "feet", "vdc": "volts", "ma": "milliamp", "mbs": "megabytes/s",
    "mhz" : "megahertz", "uf": "microfarads", "pf": "picofarads", "vac": "volts", "deg": "degrees", "mfd": "millifarads", "volt": "volts",
    "oz"  : "ounces", "ml": "milliliters", "g": "grams"
}
quantity_identifiers_str = r'pcs|pairs|Pcs|PCS|pieces|piece|pc|[xX](?![0-9]+|\s[0-9]+(?![a-z])|[a-zA-Z]+)|\*(?!\s?[0-9]+)|pack|set(?! of)|per lot'
measurement_regex = re.compile(r'\b(?<!\d\-)(\d*\.?\d+)[\s\-\(\[\//]*(' + "|".join(measurement_list) + r')[\s\//]{0,1}(?!\-)\b')
measurement_special_case_1 = re.compile(r'(?<!\d\-)(\d*\.?\d+)(' + "|".join(measurement_list) + r')([\d\w]*)')
quantity_regex = re.compile(r'(?<!#)(\d+,?\d+\s?)(' + quantity_identifiers_str + ')[\s\)\-]*')
quantity_special_case_1 = re.compile(r"(\d+\/\d+)\s?(?=" + quantity_identifiers_str + ")")
quantity_special_case_2 = re.compile("(pack\s?of|lot\s?[oO]f |quantity\s?of|quantity\-|set of|qty\.?|total:?)\s?\(?(\d+)\)?")
quantity_special_case_3 = re.compile("\(?(\d+)\)?\s?(?=lot)")
quantity_special_case_4 = re.compile("(\d+)\/ea")
dimensions = re.compile("\(?(\d*\.?\d+)\s?[*x]\s?(\d*\.?\d+)\)?")
pairs_regex = re.compile(r'(([a-zA-Z0-9]+\s){2}|([a-zA-Z0-9]+\s){1})(and|&)((\s[a-zA-Z0-9]+){2}|(\s[a-zA-Z0-9]+){1})')
range_regex = re.compile(r'\s([0-9\.]+)\-([0-9\.]+)\s?(v|mm|nm)')
product_num = re.compile(r'\b([a-z0-9]+\-\S*\d+\S*|[\d.]+\-[\d.]+\-\S+(?![a-z]+)|[\d.]+\-[\d.]+(?![a-z]+)|\d+[a-z]\d+|[a-z]+[0-9]{1,}\S+)\b')
possible_ranges = re.compile(r'\b(?<!\-)([\d\w]+)\-([\d\w]+)(?!\-)\b')
measurement_range_regex = re.compile(r'\b(\d*\.?\d+)\-(\d*\.?\d+)[\s\-\(\[]*(' + "|".join(measurement_list) + r')[\s\//]{0,1}(?!\-)\b')
date_regex = re.compile(r"^(SOLD.+,\s\d{4})")


def check_groups(s, r=None):
    rtr = []
    valid = False
    if not r:
        r = measurement_special_case_1.search(s)
    if not r:
        return []
    m, u, other = r.groups()
    other_rslt = measurement_special_case_1.search(other)
    if not other_rslt:
        return rtr
    if other_rslt.groups()[2]:
        rtr = rtr + check_groups(other, other_rslt)
    title = s
    measurement_1 = m + u
    m_1_rslt = measurement_regex.findall(measurement_1)
    if not rtr:
        other_rslt = measurement_regex.findall(other)
    else:
        other_rslt = rtr
    rtr = set(rtr)
    if m_1_rslt and other_rslt:
        start_position = r.start()
        if start_position > 0:

            if title[start_position - 1] in " :":
                valid = True
        else:
            valid = True
        if valid:
            rtr.add(m_1_rslt[0])
            for rslt in other_rslt:
                rtr.add(rslt)
    return list(rtr)


def handle_measurements(measurement_results, rtr_dict=None):
    if not rtr_dict or type(rtr_dict) != dict:
        rtr_dict = {}
    for i, u in measurement_results:
        if u not in measurement_dict:
            long_form = u
        else:
            long_form = measurement_dict[u]
            if long_form[-1] != 's' and long_form not in ["megahertz", "hertz", "feet", "volts ac", "volts dc"]:
                long_form += 's'
        try:
            float_i = float(i)
        except:
            try:
                float_i = [float(x) for x in i.split("-")]
            except:
                pass
        try:
            if long_form not in rtr_dict:
                if type(float_i) == float:
                    rtr_dict[long_form] = [float_i]
                else:
                    rtr_dict[long_form] = float_i
            else:
                if type(float_i) == float:
                    rtr_dict[long_form].append(float_i)
                else:
                    rtr_dict[long_form] = rtr_dict[long_form] + float_i

        except:
            pass
    return rtr_dict


def get_measurements(title):
    rtr_dict = handle_measurements(measurement_regex.findall(title))
    special_case = check_groups(title)
    if special_case:
        rtr_dict = handle_measurements(special_case, rtr_dict)
        for m, u in special_case:
            title = title.replace(m + u, " ")
        title = " ".join(title.split())
    title = " ".join(measurement_regex.sub(" ", title).split())
    return title, rtr_dict


def get_measurements_range(title):
    ranges = measurement_range_regex.findall(title)
    measurements_result = []
    for _range in ranges:
        unit = _range[2]
        measurements_result.append((_range[0], unit))
        measurements_result.append((_range[1], unit))

    rtr_dict = handle_measurements(measurements_result)
    title = " ".join(measurement_range_regex.sub(" ", title).replace(" - ", " ").split())

    return title, rtr_dict


def get_dimensions(title):
    rtr = []
    for x, y in dimensions.findall(title):
        rtr.append(x)
        rtr.append(y)

    title = dimensions.sub(" ", title)

    return title, rtr


def get_quantity(title):
    rtr = []
    pairs_triggered = False

    for i in quantity_special_case_1.findall(title):
        if r'/' in i:
            tmp_i = i.split("/")
            for value in tmp_i:
                try:
                    rtr.append({"all": int(value.replace(",", ""))})
                except:
                    pass
            title.replace(i, "")

    for i, u in quantity_regex.findall(title):
        i = i.strip()
        if u == "pairs" or u == "pair":
            pairs_result = pairs_regex.findall(title)
            for pair in pairs_result:
                pairs_triggered = True
                if rtr:
                    num_denom = rtr[0]["all"]
                else:
                    num_denom = int(i.replace(",", ""))
                if pair[0] and pair[4]:
                    rtr.append({pair[0].strip(): num_denom // 2, pair[4].strip(): num_denom // 2})
                else:
                    if pair[0]:
                        rtr.append({pair[0].strip(): num_denom // 2, pair[5].strip(): num_denom // 2})
                    elif pair[4]:
                        rtr.append({pair[1].strip(): num_denom // 2, pair[4].strip(): num_denom // 2})
                    else:
                        rtr.append({pair[1].strip(): num_denom // 2, pair[5].strip(): num_denom // 2})
        elif not rtr or pairs_triggered:
            rtr.append({"all": int(i.replace(",", ""))})
            if pairs_triggered:
                for k in rtr[0].keys():
                    rtr[0][k] = int(i.replace(",", "")) // 2

    for u, i in quantity_special_case_2.findall(title):
        rtr.append({"all": int(i.replace(",", ""))})
    for i in quantity_special_case_3.findall(title):
        rtr.append({"all": int(i.replace(",", ""))})
    for i in quantity_special_case_4.findall(title):
        pairs_result = pairs_regex.findall(title)
        for pair in pairs_result:
            num_denom = int(i.replace(",", ""))
            if pair[0] and pair[4]:
                rtr.append({pair[0].strip(): num_denom, pair[4].strip(): num_denom})
            else:
                if pair[0]:
                    rtr.append({pair[0].strip(): num_denom, pair[5].strip(): num_denom})
                elif pair[4]:
                    rtr.append({pair[1].strip(): num_denom, pair[4].strip(): num_denom})
                else:
                    rtr.append({pair[1].strip(): num_denom, pair[5].strip(): num_denom})
    if not rtr:
        rtr = [{"all": [1]}]
    if rtr[0] == {"all": [0]}:
        rtr[0] = [{"all": [1]}]
    tmp_dict = {}
    for i in rtr:
        for k in i.keys():
            if type(i[k]) == list:
                to_use = i[k][0]
            else:
                to_use = i[k]
            if k not in tmp_dict:
                tmp_dict[k] = to_use
            else:
                tmp_dict[k] = max(to_use, tmp_dict[k])

    rtr = tmp_dict
    title = quantity_special_case_2.sub(" ", title)
    title = quantity_special_case_3.sub(" ", title)
    title = quantity_special_case_4.sub(" ", title)
    title = quantity_regex.sub(" ", title)
    title = " ".join(title.split())

    return title, rtr


def run_all(title):
    rtr = {}
    # title, rtr["measurements"] = get_measurements_range(title)
    title, rtr["measurements"] = get_measurements(title)
    # keys_changed = []
    # if rtr["measurements"] and tmp_measure:
    #     for i in tmp_measure.keys():
    #         if i in rtr["measurements"]:
    #             cur_measurements = set(rtr["measurements"][i])
    #             for m in tmp_measure[i]:
    #                 cur_measurements.add(m)
    #             rtr["measurements"][i] = list(cur_measurements)
    #         else:
    #             rtr["measurements"][i] = tmp_measure[i]
    # else:
    #     rtr["measurements"] = tmp_measure

    title, rtr["quantity"] = get_quantity(title)
    return title, rtr
