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


from platform_bib_parser import (
    get_locations,
    get_bibNo,
    get_rec_type,
    get_blvl,
    get_isbns,
    get_item_form,
    has_research_call_number,
    get_branch_call_number,
    has_call_number,
    get_normalized_title,
    is_marked_for_deletion,
    has_oclc_number,
    has_lc_number,
    get_timestamp
)
from platform import AuthorizeAccess, PlatformSession, platform_status_interpreter
from research_locations import RES_CODES
from utils import save2csv


# set up logger
log_console_format = "[%(levelname)s]: %(message)s"

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_console_format))

file_handler = RotatingFileHandler(
    ".\\logs\\dedup.log", maxBytes=1024 * 1024, backupCount=10
)
formatter = logging.Formatter(
    "[%(levelname)s] - %(asctime)s - %(name)s - : %(message)s in %(filename)s:%(lineno)d"
)
file_handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(console_handler)
logger.addHandler(file_handler)


def is_valid_bib_type(rec_type, blvl, item_form):
    # lang mat only
    if rec_type == "a" and blvl == "m" and item_form in [" ", "d"]:
        return True
    else:
        return False


def is_ebook(rec_type, blvl, item_form):
    if rec_type == "a" and blvl == "m" and item_form == "o":
        return True


def has_call_number_conflict(call1, call2):
    if call1 == call2:
        return False
    elif call1 is None or call2 is None:
        return False
    else:
        return True


def has_title_discrepancies(bib1, bib2):
    title1 = get_normalized_title(bib1)
    title2 = get_normalized_title(bib2)
    if title1 != title2:
        return True
    else:
        return False


def determine_records_score(bibs):
    bib_scores = dict()
    for bid, bib in bibs.items():
        logger.debug(f"Analyzing score of bib b{bid}a")
        score = 0
        if not is_marked_for_deletion(bib):
            logger.debug(f"b{bid}a + 1 (not marked for del)")
            score += 1

        if has_call_number(bib):
            logger.debug(f"b{bid}a + 1 (has call num)")
            score += 2

        if has_oclc_number(bib):
            logger.debug(f"b{bid}a + 1 (has oclc num)")
            score += 1

        if has_lc_number(bib):
            logger.debug(f"b{bid}a + 1 (has lc num)")
            score += 1

        bib_scores[bid] = score

    # # take into consideration record updates
    # timestamps = dict()
    # for bid, bib in bibs.items():
    #     timestamp = get_timestamp(bib)
    #     timestamps[bid] = timestamp

    # ord_timestamps = sorted(timestamps.values())
    # newest_timestamp = ord_timestamps[0]
    # for bid, timestamp in timestamps.items():
    #     if timestamp == newest_timestamp:
    #         score = bib_scores[bid]
    #         bib_scores[bid] = score + 1
    #         logger.debug(f"b{bid}a + 1 (newest)")

    return bib_scores


def highest_score(bib_scores):
    highest_score = sorted(bib_scores.values(), reverse=True)[0]
    for k, v in bib_scores.items():
        if v == highest_score:
            return k


def create_dup_report(dup_bibs):

    logger.info(f"Branch duplicates: {dup_bibs.keys()}")
    bibs_scores = determine_records_score(dup_bibs)
    logger.info(f"Records scores : {bibs_scores}")
    dst_bid = highest_score(bibs_scores)
    logger.info(f"Best record: b{dst_bid}a")


    dst_bib = dup_bibs[dst_bid]
    dst_callnum = get_branch_call_number(dst_bib)
    del dup_bibs[dst_bid]

    logger.info(f"Destination bib call number: {dst_callnum}")
    for bid, bib in dup_bibs.items():
        callnum = get_branch_call_number(bib)
        if has_call_number_conflict(dst_callnum, callnum):
            logger.info(f"Call number conflict: {dst_callnum} vs {callnum}")
            save2csv(
                ".\\files\\branch-ord-191201.callnum-conflict.csv",
                [f"b{dst_bid}a", f"b{bid}a", dst_callnum, callnum],
            )
        elif has_title_discrepancies(dst_bib, bib):
            logger.info(f"Title conflict: b{dst_bid}a-b{bid}a")
            save2csv(
                ".\\files\\branch-ord-191201.title-conflict.csv",
                [f"b{dst_bid}a", f"b{bid}a", dst_callnum, callnum],
            )
        else:
            logger.info(f"Clean duplicates: b{dst_bid}a-b{bid}a")
            save2csv(
                ".\\files\\branch-ord-191201.confirmed-branch-dups.csv",
                [f"b{dst_bid}a", f"b{bid}a", dst_callnum, callnum, "awaiting"],
            )


def has_research_location(record):
    for loc in get_locations(record):
        if loc in RES_CODES:
            return True


def parse_results(matched_records):
    # reject bibs with call number issues
    # reject mixed and research bibs
    branch_matches = dict()
    matched_bids = []
    for record in matched_records:
        bid = get_bibNo(record)
        rec_type = get_rec_type(record)
        blvl = get_blvl(record)
        item_form = get_item_form(record)
        isbns = get_isbns(record)

        # check if ebook and save for separate report
        if is_ebook(rec_type, blvl, item_form):
            logger.info(f"Identified ebook: bid: b{bid}a , isbns={isbns}")
            save2csv(
                "./files/branch-ord-191201.ebook-report.csv",
                [f"b{bid}a", ",".join(isbns)],
            )
        if not is_valid_bib_type(rec_type, blvl, item_form):
            logger.info(f"Rejecting invalid item format bib b{bid}a")
        elif has_research_call_number(record):
            logger.info(f"Rejecting mixed/research bib b{bid}a (852)")
        elif has_research_location(record):
            logger.info(f"Rejecting research bib b{bid}a (location)")
        elif is_marked_for_deletion(record):
            logger.info(f"Rejecting marked for deletion bib b{bid}a")
        else:
            branch_matches[bid] = record
            matched_bids.append(bid)

    logger.info(f"Found {len(matched_bids)} branch matches.")
    if len(branch_matches) > 1:
        create_dup_report(branch_matches)
        raise Exception("The END")


def query_platform(src, token):
    with PlatformSession(
        base_url="https://platform.nypl.org/api/v0.1", token=token
    ) as session:
        logger.info("Platform session open.")
        with open(src, "r") as src_file:
            reader = csv.reader(src_file)
            for row in reader:
                sbid = row[0]
                isbns = row[1].split(",")
                if isbns != [""]:
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

                    parse_results(matched_bibs)
                else:
                    logger.info("Skipping query - no ISBN in the source.")


if __name__ == "__main__":
    import os
    from marc_parser import marc2list

    src = "./files/branch-brief-dups-191201.mrc_clean_rev.mrc"
    dst = "./files/branch-brief-191201.csv"
    creds_fh = os.path.join(
        os.environ["USERPROFILE"], ".platform\\bookops_platform.json"
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
    query_platform(dst, token)
