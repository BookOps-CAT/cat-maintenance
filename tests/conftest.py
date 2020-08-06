import json

import pytest


@pytest.fixture
def test_bib():
    with open(".\\test_files\\bib.json") as file:
        return json.load(file)


@pytest.fixture
def test_mixed_bib():
    with open(".\\test_files\\mixed_bib.json") as file:
        return json.load(file)
