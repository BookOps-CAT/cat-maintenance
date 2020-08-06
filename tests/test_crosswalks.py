from scripts import platform_bib_parser as pbp


def test_get_leader(test_bib):
    assert pbp.get_leader(test_bib) == "00000pam  2200361 a 4500"


def test_get_rec_type(test_bib):
    assert pbp.get_rec_type(test_bib) == "a"


def test_get_blvl(test_bib):
    assert pbp.get_blvl(test_bib) == "m"


def test_get_isbn(test_bib):
    assert pbp.get_isbns(test_bib) == ["0679894608", "0679994602"]


def test_get_tag_008(test_bib):
    assert pbp.get_tag_008(test_bib) == "000313s2000    nyua   j      000 1 eng  pam a "


def test_get_item_form(test_bib):
    assert pbp.get_item_form(test_bib) == " "