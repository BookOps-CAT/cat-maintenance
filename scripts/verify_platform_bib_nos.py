"""
Use to check if NYPL Platform has given Sierra bib numbers
"""
import os
import json
import sys

from bookops_nypl_platform import PlatformToken, PlatformSession
from utils import save2csv


def get_token(client_id, client_secret, oauth_server):
    token = PlatformToken(client_id, client_secret, oauth_server)
    return token


def extract_sierra_no(value):
    bibNo = value[-10:-2]
    return f"b{bibNo}a"


def missing_sierra_numbers(log_fh):
    with open(log_fh, "r", errors="surrogateescape") as logfile:
        for line in logfile:
            if "NYPL Platform request (404)" in line:
                bibNo = extract_sierra_no(line)
                yield bibNo


def check_bib_in_platform(session, bibNo):
    response = session.get_bib(bibNo)
    return response


def verify(log_fh, token):
    with PlatformSession(authorization=token) as session:
        bibNos = missing_sierra_numbers(log_fh)
        for bibNo in bibNos:
            result = check_bib_in_platform(session, bibNo)
            print(f"{bibNo}:{result.status_code}")
            save2csv("files/platform-bib-state.csv", [bibNo, result.status_code])


if __name__ == "__main__":
    fh = os.path.join(os.environ["USERPROFILE"], ".platform/tomasz_platform.json")
    with open(fh, "r") as file:
        creds = json.load(file)
        token = get_token(
            creds["client-id"], creds["client-secret"], creds["oauth-server"]
        )
    log_fh = sys.argv[1]
    verify(log_fh, token)
