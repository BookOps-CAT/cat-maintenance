import json

import pytest


@pytest.fixture
def test_bib():
    with open(".\\test_files\\bib.json") as file:
        data = json.load(file)
        return data
