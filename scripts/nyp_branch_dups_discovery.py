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
    get_encoding_level,
    get_isbns,
    get_item_form,
    has_branch_call_number,
    has_research_call_number,
    get_branch_call_number,
    has_call_number,
    get_normalized_title,
    get_oclc_number,
    is_marked_for_deletion,
    has_oclc_number,
    has_lc_number,
    has_082_tag,
    has_505_tag,
    has_520_tag,
    has_050_tag,
    has_national_library_authentication_code,
    has_subject_tags,
    is_dlc_record,
    get_timestamp,
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
# logger.addHandler(file_handler)


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


def score_record_level(bib):
    lvl = get_encoding_level(bib)
    if lvl in (" ", "I", "1"):
        return 2
    elif lvl in ("3", "4", "5", "7", "8", "K"):
        return 1
    else:
        return 0


def score_isbns(bib):
    isbns = get_isbns(bib)
    return len(isbns)


def determine_records_score(bibs):
    bib_scores = dict()
    for bid, bib in bibs.items():
        logger.debug(f"Analyzing score of bib b{bid}a")
        score = 0
        if not is_marked_for_deletion(bib):
            logger.debug(f"b{bid}a +1 (not marked for del)")
            score += 2

        if has_call_number(bib):
            logger.debug(f"b{bid}a +1 (has call num)")
            score += 2

        if has_oclc_number(bib):
            logger.debug(f"b{bid}a +1 (has oclc num)")
            score += 2

        if has_lc_number(bib):
            logger.debug(f"b{bid}a +1 (has lc num)")
            score += 1

        if has_082_tag(bib):
            logger.debug(f"b{bid}a +1 (has 082)")
            score += 1

        if has_050_tag(bib):
            logger.debug(f"b{bid}a +1 (has 050)")
            score += 1

        if has_505_tag(bib):
            logger.debug(f"b{bid}a +1 (has 505)")
            score += 1

        if has_520_tag(bib):
            logger.debug(f"b{bid}a +1 (has 520)")
            score += 1

        if has_national_library_authentication_code(bib):
            logger.debug(f"b{bid}a +1 (is PCC)")
            score += 2

        if is_dlc_record(bib):
            logger.debug(f"b{bid}a +1 (is DLC)")
            score += 2

        if has_subject_tags(bib):
            logger.debug(f"b{bid}a +1 (has subjects)")
            score += 1

        rec_lvl_score = score_record_level(bib)
        logger.debug(f"b{bid}a +{rec_lvl_score} (level score)")
        score += rec_lvl_score

        isbn_score = score_isbns(bib)
        logger.debug(f"b{bid}a + {isbn_score} (isbn score)")

        bib_scores[bid] = score

    # take into consideration record updates
    timestamps = dict()
    for bid, bib in bibs.items():
        timestamp = get_timestamp(bib)
        timestamps[bid] = timestamp
    logger.debug(f"Timestamps: {timestamps}")

    ord_timestamps = sorted(timestamps.values(), reverse=True)
    logger.debug(f"Ordered timestamps: {ord_timestamps}")
    newest_timestamp = ord_timestamps[0]
    for bid, timestamp in timestamps.items():
        if timestamp == newest_timestamp:
            score = bib_scores[bid]
            bib_scores[bid] = score + 1
            logger.debug(f"b{bid}a + 1 (newest)")

    return bib_scores


def highest_score(bib_scores):
    highest_score = sorted(bib_scores.values(), reverse=True)[0]
    for k, v in bib_scores.items():
        if v == highest_score:
            return k


def create_dup_report(dup_bibs):

    oclc_fh = ".\\files\\reports\\former-mixed-bibs.REPORT_OCLC-NUMERS.csv"

    logger.info(f"Branch duplicates: {dup_bibs.keys()}")
    bibs_scores = determine_records_score(dup_bibs)
    logger.info(f"Records scores : {bibs_scores}")
    dst_bid = highest_score(bibs_scores)
    logger.info(f"Best record: b{dst_bid}a")

    dst_bib = dup_bibs[dst_bid]
    dst_callnum = get_branch_call_number(dst_bib)
    dst_title = get_normalized_title(dst_bib)

    # save for later OCLC holdings cleanup
    oclc_no = get_oclc_number(dst_bib)
    if oclc_no is not None:
        save2csv(oclc_fh, [oclc_no])

    del dup_bibs[dst_bid]

    logger.info(f"Destination bib call number: {dst_callnum}")
    for bid, bib in dup_bibs.items():
        callnum = get_branch_call_number(bib)
        title = get_normalized_title(bib)

        # save involved oclc number for later cleanup of OCLC holdings
        oclc_no = get_oclc_number(bib)
        if oclc_no is not None:
            save2csv(oclc_fh, [oclc_no])

        if has_call_number_conflict(dst_callnum, callnum):
            logger.info(f"Call number conflict: {dst_callnum} vs {callnum}")

            save2csv(
                ".\\files\\reports\\former-mixed-bibs.REPORT_CALLNUM-CONFLICT.csv",
                [f"b{dst_bid}a", f"b{bid}a", dst_callnum, callnum, "awaiting"],
            )

        elif has_title_discrepancies(dst_bib, bib):
            logger.info(f"Title conflict: b{dst_bid}a-b{bid}a")

            save2csv(
                ".\\files\\reports\\former-mixed-bibs.REPORT_TITLE-CONFLICT.csv",
                [f"b{dst_bid}a", f"b{bid}a", dst_title, title, "awaiting"],
            )
        else:
            logger.info(f"Clean duplicates: b{dst_bid}a-b{bid}a")

            save2csv(
                ".\\files\\reports\\former-mixed-bibs.REPORT_CONFIRMED-DUPS.csv",
                [f"b{dst_bid}a", f"b{bid}a", dst_callnum, callnum, "awaiting"],
            )


def has_research_location(record):
    for loc in get_locations(record):
        if loc in RES_CODES:
            return True


def has_only_branch_locations(record):
    only_branches = True
    for loc in get_locations(record):
        if loc in RES_CODES:
            only_branches = False
    return only_branches


def has_ebook_location(record):
    if "ia" in get_locations(record):
        return True
    else:
        return False


def identify_library(record):
    research = False
    branches = False

    bid = get_bibNo(record)
    logger.debug(f"Idenfifying record b{bid}a.")

    if has_research_call_number(record):
        research = True
    if has_research_location(record):
        research = True
    if has_branch_call_number(record):
        branches = True
    if has_only_branch_locations(record):
        branches = True

    if has_ebook_location(record):
        library = "neutral"
    elif research is True and branches is not True:
        library = "research"
    elif research is True and branches is True:
        library = "mixed"
    elif research is False and branches is True:
        library = "branches"
    elif research is False and branches is False:
        library = "neutral"

    return library


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
        library = identify_library(record)
        logger.debug(f"Record b{bid}a identified as {library}.")

        # check if ebook and save for separate report
        if is_ebook(rec_type, blvl, item_form):
            logger.info(f"Identified ebook: bid: b{bid}a , isbns={isbns}")
            save2csv(
                "./files/reports/former-mixed-bibs.REPORT_EBOOKS.csv",
                [f"b{bid}a", ",".join(isbns)],
            )
        elif library != "branches":
            logger.info(
                f"Rejecting wrong library bib: b{bid}a identified as {library}.")
        elif not is_valid_bib_type(rec_type, blvl, item_form):
            logger.info(f"Rejecting invalid item format bib b{bid}a")
        elif is_marked_for_deletion(record):
            logger.info(f"Rejecting marked for deletion bib b{bid}a")
        else:
            branch_matches[bid] = record
            matched_bids.append(bid)

    logger.info(f"Found {len(matched_bids)} branch matches.")
    if len(matched_bids) > 1:
        create_dup_report(branch_matches)
        # raise Exception("The END")


def query_platform(src, token):
    with PlatformSession(
        base_url="https://platform.nypl.org/api/v0.1", token=token
    ) as session:
        logger.info("Platform session open.")
        with open(src, "r") as src_file:
            reader = csv.reader(src_file)
            for row in reader:
                sbid = f"{row[0][:-1]}a"
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

                    logger.debug(f"Found {len(matched_bibs)} matches for {sbid}.")
                    parse_results(matched_bibs)
                else:
                    logger.info("Skipping query - no ISBN in the source.")


if __name__ == "__main__":
    import os
    from marc_parser import marc2list

    src = "./files/src_mrc/msplit00000042.mrc"
    dst = "./files/src_csv/msplit00000042.csv"
    creds_fh = os.path.join(
        os.environ["USERPROFILE"], ".platform\\tomasz_platform.json"
    )
    marc2list(src, dst)
    with open(creds_fh, "r") as file:
        creds = json.load(file)

    auth = AuthorizeAccess(
        client_id=creds["client-id"],
        client_secret=creds["client-secret"],
        oauth_server="https://isso.nypl.org",
    )

    token = auth.get_token()
    query_platform(dst, token)
