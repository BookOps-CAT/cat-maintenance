def get_locations(bib=None):
    """
    extracts meta from Platform results
    args:
        results (json format)
    return:
        list of inhouse bibs meta
    """
    if bib is not None:
        locations = [x.get("code") for x in bib.get("locations")]
        return locations
    else:
        return


def get_bibNo(bib=None):
    if bib is not None:
        bid = bib.get("id")
        return bid
    else:
        return


def get_leader(bib=None):
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("fieldTag") == "_":
                return field.get("content")


def get_rec_type(bib=None):
    rec_type = None
    if bib is not None:
        leader = get_leader(bib)
        rec_type = leader[6]
    return rec_type


def get_blvl(bib=None):
    if bib is not None:
        leader = get_leader(bib)
        blvl = leader[7]
        return blvl


def get_tag_008(bib):
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "008":
                return field.get("content")


def get_item_form(bib=None):
    if bib is not None:
        tag_008 = get_tag_008(bib)
        return tag_008[23]


def get_isbns(bib=None):
    if bib is not None:
        return bib.get("standardNumbers")


if __name__ == "__main__":
    import json

    fh = ".\\files\\plat_response.json"
    with open(fh, "r") as file:
        data = json.load(file)
        leader = print(get_leader(data))
