import pytest

from scripts import nyp_branch_dups_discovery as dd


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (".b220317434", "b220317434"),
        (".b202278372 07-06-20 06-20-2014 10:13", "b202278372"),
        ("test", None),
        ("a220317434", None),
    ],
)
def test_parse_bibNo(test_input, expected):
    assert dd.parse_bibNo(test_input) == expected


@pytest.mark.parametrize(
    "rec_type,blvl,item_form,expected",
    [
        ("a", "m", " ", True),
        ("a", "m", "d", True),
        ("a", "a", "o", False),
        ("a", "a", "b", False),
        ("c", "a", " ", False),
        ("c", "a", "d", False),
        ("a", "a", " ", False)
    ],
)
def test_is_valid_bib_type(rec_type, blvl, item_form, expected):
    assert dd.is_valid_bib_type(rec_type, blvl, item_form) == expected
