"""
Sheet to MARC BPL laptop crosswalk
"""

from collections import namedtuple
import csv
from datetime import date

from pymarc import Record, Field

from utils import save2marc


MapData = namedtuple(
    "MapData", ["type", "comp_name", "serial", "asset", "wlan", "barcode"]
)


def source_reader(fh: str):
    for row in map(MapData._make, csv.reader(open(fh, "r"))):
        if row.type == "HP EliteBook 840 G6":
            yield row


def determine_lap_num(name):
    return name[7:9]


def determine_locker_num(name):
    return f"Locker number {name[-4:]}"


def construct_item_note(locker, laptop, data):
    return f"Bay #: {locker} - Name: 32_PUBLAP{laptop} - Serial number: {data.serial} - Asset #: {data.asset} - WLAN MAC: {data.wlan}"


def make_bib(data: namedtuple):
    bib = Record()
    tags = []
    locker_num = determine_locker_num(data.comp_name)

    # leader
    bib.leader = "00000nrm a2200000Mi 4500"

    # 008 tag
    dateCreated = date.strftime(date.today(), "%y%m%d")
    tags.append(
        Field(tag="008", data=f"{dateCreated}s2019    xx             00 r|und d")
    )

    # 099 tag
    tags.append(Field(tag="099", indicators=[" ", " "], subfields=["a", "LAPTOP"]))

    # 245 tag
    tags.append(
        Field(tag="245", indicators=["0", "0"], subfields=["a", f"{locker_num}."])
    )

    # single sub A 246 tags
    lap_num = determine_lap_num(data.comp_name)
    alt_titles = [
        "Laptop circulation",
        "Laptops in the branches",
        "Wireless laptops",
        "Circulating laptops",
        "Laptop computers",
        f"32_PUBLAP{lap_num}",
    ]
    for at in alt_titles:
        tags.append(Field(tag="246", indicators=["3", " "], subfields=["a", at]))

    # complex 246 tags

    tags.append(
        Field(
            tag="246",
            indicators=["3", " "],
            subfields=["a", f"{data.type}.", "n", locker_num],
        )
    )
    tags.append(
        Field(
            tag="246",
            indicators=["3", " "],
            subfields=["a", f"{data.type}.", "n", f"32_PUBLAP{lap_num}"],
        )
    )

    # 300 tag
    tags.append(
        Field(tag="300", indicators=[" ", " "], subfields=["a", "1 laptop computer"])
    )

    # 500 tag
    tags.append(
        Field(
            tag="500",
            indicators=[" ", " "],
            subfields=["a", f"Serial number: {data.serial}"],
        )
    )

    # 960 tag
    item_note = construct_item_note(locker_num, lap_num, data,)
    tags.append(
        Field(
            tag="960",
            indicators=[" ", " "],
            subfields=[
                "l",
                "32lap",
                "t",
                "49",
                "r",
                "7",
                "q",
                "7",
                "s",
                "g",
                "n",
                f"{item_note}",
            ],
        )
    )

    # commnad line tag
    tags.append(
        Field(tag="949", indicators=[" ", " "], subfields=["a", f"*b2=7;bn=32;"])
    )

    for t in tags:
        bib.add_ordered_field(t)

    return bib


def create_bibs(src_fh: str, out_fh: str):
    reader = source_reader(src_fh)
    for row in reader:
        bib = make_bib(row)
        print(bib)
        save2marc(out_fh, bib)


if __name__ == "__main__":
    src_fh = "./files/ConeyIslandLaptops.csv"
    out_fh = "./files/ConeyIslandLaptops.mrc"
    create_bibs(src_fh, out_fh)
