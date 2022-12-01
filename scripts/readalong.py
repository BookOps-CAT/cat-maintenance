from pymarc import MARCReader, Field

try:
    from scripts.utils import save2marc
except ImportError:
    from utils import save2marc


def change_to_je(callNo: Field) -> Field:
    new_subs = []
    for sub in callNo.get_subfields("a"):
        if sub.strip() == "J":
            sub = "J-E"
        if sub.strip() != "FIC":
            new_subs.extend(["a", sub])

    return Field(tag="099", indicators=[" ", " "], subfields=new_subs)


def process_file(fh: str):
    with open(fh, "rb") as marcfile:
        reader = MARCReader(marcfile)
        for bib in reader:

            # change call number
            callNo = bib["099"]
            new_callNo = change_to_je(callNo)
            bib.remove_field(callNo)
            bib.add_ordered_field(new_callNo)

            # add classification change
            bib.add_ordered_field(
                Field(
                    tag="947",
                    indicators=["1", " "],
                    subfields=[
                        "a",
                        "tak",
                        "n",
                        f"Call number changed from {callNo.value()} to {new_callNo.value()} on 12/01/2022",
                    ],
                )
            )

            # command tag
            opac_code = bib["998"]["e"].strip()
            if opac_code != "-":
                command = f"*b2=8;b3=opac_code;"
            else:
                command = f"*b2=8;"
            bib.add_ordered_field(
                Field(tag="949", indicators=[" ", " "], subfields=["a", command])
            )

            save2marc("./files/READALONG-JE-PROC.mrc", bib)


if __name__ == "__main__":
    process_file("./files/READALONG-JE-CallChange.mrc")
