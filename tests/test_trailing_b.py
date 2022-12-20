from pymarc import Record, Field

import pytest

from scripts.trailing_b import (
    add_ocn_to_001,
    enforce_oclc_symbol_in_003,
    has_ocn,
    normalize_ocn,
    ocn_as_control_no,
)


@pytest.fixture
def stub_bib():
    bib = Record()
    bib.leader = "01000nam a2200313ua 4500"
    bib.add_field(Field(tag="245", indicators=["0", "0"], subfields=["a", "Test file"]))
    return bib


def test_enforce_oclc_symbol_in_003_missing_tag(stub_bib):
    enforce_oclc_symbol_in_003(stub_bib)

    assert stub_bib["003"].data == "OCoLC"


def test_enforce_oclc_symbol_in_003_present_tag(stub_bib):
    stub_bib.add_field(Field(tag="003", data="FOO"))

    enforce_oclc_symbol_in_003(stub_bib)
    assert stub_bib["003"].data == "OCoLC"
    assert len(stub_bib.get_fields("003")) == 1


def test_add_ocn_to_001_missing_tag(stub_bib):
    add_ocn_to_001(stub_bib, "1234")

    assert stub_bib["001"].data == "1234"


def test_add_ocn_to_001_present_tag(stub_bib):
    stub_bib.add_field(Field("001", data="foo1"))

    add_ocn_to_001(stub_bib, "1234")

    assert stub_bib["001"].data == "1234"
    assert len(stub_bib.get_fields("001")) == 1


@pytest.mark.parametrize(
    "arg,expectation", [("(WaOLN)1234", False), ("(OCoLC)1234B", True)]
)
def test_has_ocn_tag_present(arg, expectation):
    field = Field(tag="035", indicators=[" ", " "], subfields=["a", arg])

    assert has_ocn(field) == expectation


def test_has_ocn_tag_missing():
    assert has_ocn(None) is False


def test_has_ocn_subfield_missing():
    field = Field(tag="035", indicators=[" ", " "], subfields=["z", "foo"])
    assert has_ocn(field) is False


@pytest.mark.parametrize(
    "arg,expectation",
    [
        ("(OCoLC)1234", "1234"),
        ("(OCoLC)1234B", "1234"),
        ("(OCoLC) 1234B", "1234"),
        ("(OCoLC) 1234B ", "1234"),
        ("(OCoLC)1234 ", "1234"),
    ],
)
def test_normalize_ocn(arg, expectation):
    assert normalize_ocn(arg) == expectation


def tests_normalize_ocn_invalid_id():
    with pytest.raises(ValueError):
        normalize_ocn("(WaOLN)")


def test_normalize_ocn_scrambled_id():
    with pytest.raises(ValueError):
        normalize_ocn("(OCoLC)ocn1234")
