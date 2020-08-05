"""
A script to run duplication report for NYPL branch materials

1. A file of MARC records with orders created since Dec 1, 2019 for branch mat was created.
2. A list of bibs and their ISBNs has been created
3. NYPL Platform was queried for each ISBN and branch records only were matched to;
    the results were dedeuped
4. Exclude non-print, eBooks, serials, etc.


Issues:
- any discrepancies between Sierra and Platform
- call number discrepancies
- book club sets
- young adult vs juvenile bib
- multivolume/sets isbns
- ebooks/print
- which record should be merged into?

"""

import csv
import json
import logging
from logging.handlers import RotatingFileHandler

from pymarc import MARCReader

from patform_bib_parser import (
    get_locations,
    get_bibNo,
    get_rec_type,
    get_blvl,
    get_isbns,
    get_item_form,
)
from platform import AuthorizeAccess, PlatformSession, platform_status_interpreter


# set up logger
log_file_format = "[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s in %(filename)s:%(lineno)d"
log_console_format = "[%(levelname)s]: %(message)s"

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_console_format))

file_handler = RotatingFileHandler(
    ".\\logs\\dedup.log", maxBytes=1024 * 1024, backupCount=10
)
file_handler.setFormatter(logging.Formatter(log_file_format))

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def save2csv(dst_fh, row):
    """
    Appends a list with data to a dst_fh csv
    args:
        dst_fh: str, output file
        row: list, list of values to write in a row
    """

    with open(dst_fh, "a") as csvfile:
        out = csv.writer(
            csvfile,
            delimiter=",",
            lineterminator="\n",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        out.writerow(row)


def extract_isbns(data):
    isbns = []
    for d in data:
        isbn = d.split(" ")[0].strip()
        isbns.append(isbn)

    return ",".join(isbns)


def parse_bibNo(field):
    # =945  \\$a.b220317434
    bibNo = field[1:11]
    if len(bibNo) != 10:
        bibNo = None
    elif bibNo[0] != "b":
        bibNo = None
    return bibNo


def is_valid_bib_type(rec_type, blvl, item_form):
    # lang mat only
    if rec_type == "a" and blvl == "m" and item_form in [" ", "d"]:
        return True
    else:
        return False


def has_research_callnum(bib):
    if "852" in bib:
        return True
    else:
        return False


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


def is_ebook(rec_type, blvl, item_form):
    if rec_type == "a" and blvl == "m" and item_form == "o":
        return True


def produce_report(dst, matched_records):
    # reject bibs with call number issues
    # reject mixed and research bibs
    branch_matches = []
    matched_bids = []
    ebooks = []
    for record in matched_records:
        bid = get_bibNo(record)
        rec_type = get_rec_type(record)
        blvl = get_blvl(record)
        item_form = get_item_form(record)
        isbns = get_isbns(record)

        # check if ebook and save for separate report
        if is_ebook(rec_type, blvl, item_form):
            logger.info(f"Identified ebook: bid: b{bid}a , isbns={isbns}")
            ebooks.append([bid, ",".join(isbns)])

        if not is_valid_bib_type(rec_type, blvl, item_form):
            logger.info(f"Rejecting invalid item format bib b{bid}a")
        elif not has_research_callnum(record):
            branch_matches.append(record)
            matched_bids.append(bid)
        else:

            logger.info(f"Rejecting mixed/research bib b{bid}a")

    logger.info(f"Found {len(branch_matches)} branch matches.")
    if len(branch_matches) > 1:
        ord_matched_bids = sorted(matched_bids)
        logger.debug(f"Ordered matches: {ord_matched_bids}")

    # save2csv(dst, [dup_bids, dst_bid, status])


def query_platform(src, dst, token):
    with PlatformSession(
        base_url="https://platform.nypl.org/api/v0.1", token=token
    ) as session:
        logger.info("Platform session open.")
        with open(src, "r") as src_file:
            reader = csv.reader(src_file)
            for row in reader:
                sbid = row[0]
                isbns = row[1].split(",")
                logger.info(f"{sbid} request for isbns: {isbns}")
                res = session.query_bibStandardNo(isbns)
                status = platform_status_interpreter(res)
                logger.info(f"Platform response for bib {sbid}: {status}")

                matched_bibs = []
                if status == "hit":
                    for mbib in res.json()["data"]:
                        mbid = get_bibNo(mbib)
                        locs = get_locations(mbib)
                        logger.debug(
                            f"Source bib: {sbid}, matched bib: b{mbid}a matched locations: {locs}"
                        )

                        matched_bibs.append(mbib)

                produce_report(dst, matched_bibs)


if __name__ == "__main__":
    import os

    src = "./files/branch-ord-191201.test30.mrc"
    dst = "./files/branch-ord-191201.csv"
    report = "./files/branc-ord-191201.report.csv"
    creds_fh = os.path.join(
        os.environ["USERPROFILE"], ".platform\\tomasz_platform.json"
    )
    # marc2list(src, dst)
    with open(creds_fh, "r") as file:
        creds = json.load(file)

    auth = AuthorizeAccess(
        client_id=creds["client-id"],
        client_secret=creds["client-secret"],
        oauth_server="https://isso.nypl.org",
    )

    token = auth.get_token()
    query_platform(dst, report, token)
