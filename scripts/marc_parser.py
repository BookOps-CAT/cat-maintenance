from pymarc import MARCReader


from nyp_branch_dups_discovery import is_valid_bib_type
from utils import save2csv


def has_research_callnum(bib):
    if "852" in bib:
        return True
    else:
        return False


def extract_isbns(data):
    isbns = []
    for d in data:
        isbn = d.split(" ")[0].strip()
        isbns.append(isbn)

    return ",".join(isbns)


def parse_bibNo(field):
    bibNo = field[1:11]
    if len(bibNo) != 10:
        bibNo = None
    elif bibNo[0] != "b":
        bibNo = None
    return bibNo


def marc2list(src, dst):
    with open(src, "rb") as f:
        reader = MARCReader(f)
        n = 0
        for bib in reader:
            n += 1
            rec_type = bib.leader[6]
            blvl = bib.leader[7]
            item_form = bib["008"].data[23]
            valid = is_valid_bib_type(rec_type, blvl, item_form)

            if valid and not has_research_callnum(bib):
                try:
                    bibNo = bib["907"].value()
                    bibNo = parse_bibNo(bibNo)
                except AttributeError:
                    raise (f"record {n} has no sierra bib number")

                isbns = ""
                isbns_data = []
                for field in bib.get_fields("020"):
                    isbns_data.append(field.value())
                    isbns = extract_isbns(isbns_data)

                save2csv(dst, [bibNo, isbns])
