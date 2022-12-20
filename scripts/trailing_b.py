"""
This scripts fixes NYPL bibs with OCLC # in the 035 field with a trailing B (RLIN records).
When identified that record does not have 991$y or this identifier is the same as in 035,
the script moves OCN to the 001 tag, adds or replaces 003 with OCoLC and deletes if needed the
991 tag.
When 991$y is different than 035, the legacy control number in 001 is preserved and script only cleans
up the 035 tag by removing the trailing B

Requires character encoding (UTF-8) cleanup in MarcEdit before the process.
"""
import sys
import warnings


from pymarc import Field, MARCReader, Record
from utils import save2marc


def enforce_oclc_symbol_in_003(bib: Record) -> None:
    try:
        bib["003"].data = "OCoLC"
    except AttributeError:
        bib.add_ordered_field(Field(tag="003", data="OCoLC"))


def add_ocn_to_001(bib: Record, ocn: str) -> None:
    try:
        bib["001"].data = ocn
    except AttributeError:
        bib.add_field(Field(tag="001", data=ocn))


def ocn_as_control_no(bib: Record, ocn: str) -> None:
    """
    Replaces the 001 with provided OCN and adds/replaces
    the 003 tag with "OCoLC"
    """
    bib["001"].data = ocn
    enforce_oclc_symbol_in_003(bib)


def has_ocn(field: Field) -> bool:
    try:
        for sub in field.get_subfields("a"):
            if sub.startswith("(OCoLC)"):
                return True
        return False
    except AttributeError:
        return False


def normalize_ocn(value: str) -> str:
    if value.lower().strip().startswith("(ocolc)"):
        value = value[7:].strip()
    else:
        raise ValueError(f"Does not seem to be OCN. Value: {value}")
    if value.lower().endswith("b"):
        value = value[:-1].strip()

    if not value.isdigit():
        raise ValueError(f"Unable to normalize OCN: value {value}")

    return value


def fix_file(fh_in: str, fh_out: str, del_991="no") -> None:
    with open(fh_in, "rb") as marc_in:
        reader = MARCReader(marc_in)
        for bib in reader:
            ocns = []
            for field in bib.get_fields("035"):
                if has_ocn(field):
                    ocn = normalize_ocn(field["a"])
                    ocns.append(ocn)
                    field["a"] = f"(OCoLC){ocn}"

            if len(ocns) != 1:
                controlNo = bib["001"]
                warnings.warn(f"Invalid number of 035s in {controlNo}")
            else:
                add_ocn_to_001(bib, ocns[0])
                enforce_oclc_symbol_in_003(bib)

            if del_991 == "yes":
                # this field is not protected in the Backstage load table
                bib.remove_fields("991")

            bib.remove_fields("908")

            save2marc(fh_out, bib)


if __name__ == "__main__":
    fix_file(sys.argv[1], sys.argv[2], sys.argv[3])
