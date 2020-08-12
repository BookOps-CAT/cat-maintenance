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


def get_encoding_level(bib):
    if bib is not None:
        leader = get_leader(bib)
        elvl = leader[17]
        return elvl


def get_item_form(bib=None):
    if bib is not None:
        tag_008 = get_tag_008(bib)
        try:
            return tag_008[23]
        except TypeError:
            return
        except IndexError:
            return


def get_isbns(bib=None):
    if bib is not None:
        return bib.get("standardNumbers")


def has_050_tag(bib=None):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "050":
                present = True
                break
    return present


def has_505_tag(bib=None):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "505":
                present = True
                break
    return present


def has_520_tag(bib=None):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "520":
                present = True
                break
    return present


def has_subject_tags(bib=None):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") in (
                "600",
                "610",
                "611",
                "630",
                "650",
                "651",
                "655",
            ):
                present = True
                break
    return present


def has_082_tag(bib=None):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "082":
                present = True
                break
    return present


def has_research_call_number(bib):
    research = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "852":
                research = True
                break
    return research


def has_branch_call_number(bib):
    branches = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "091":
                branches = True
                break
    return branches


def has_national_library_authentication_code(bib):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "042":
                present = True
                break
    return present


def is_dlc_record(bib):
    dlc = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "040":
                for subfield in field.get("subfields"):
                    if subfield.get("content") == "DLC":
                        dlc = True
                        break

    return dlc


def get_branch_call_number(bib):
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "091":
                segments = []
                for subfield in field.get("subfields"):
                    segments.append(subfield.get("content"))
                return " ".join(segments).upper()


def get_oclc_number(bib):
    oclc_number = None
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "001":
                control_number = field.get("content")
                try:
                    oclc_number = str(int(control_number))
                except ValueError:
                    pass
                except TypeError:
                    pass
            if field.get("marcTag") == "991":
                for subfield in field.get("subfields"):
                    if subfield.get("tag") == "y":
                        oclc_number == subfield.get("content")
    return oclc_number


def has_call_number(bib):
    present = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") in ("091", "852"):
                present = True
                break
    return present


def has_oclc_number(bib):
    has_number = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "003":
                if field.get("content") == "OCoLC":
                    has_number = True
            if field.get("marcTag") == "991":
                has_number = True

    return has_number


def has_lc_number(bib):
    has_number = False
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "010":
                has_number = True
    return has_number


def get_timestamp(bib):
    timestamp = 0.0
    if bib is not None:
        for field in bib.get("varFields"):
            if field.get("marcTag") == "005":
                try:
                    timestamp = float(field.get("content"))
                except ValueError:
                    pass
                except TypeError:
                    pass
    return timestamp


def get_normalized_title(bib):
    if bib is not None:
        return bib.get("normTitle")


def is_marked_for_deletion(bib):
    if bib is not None:
        for code, field in bib["fixedFields"].items():
            if code == "31":
                if field["value"] == "d":
                    return True
                else:
                    return False


if __name__ == "__main__":
    import json

    fh = ".\\files\\plat_response.json"
    with open(fh, "r") as file:
        data = json.load(file)
        print(is_marked_for_deletion(data))
