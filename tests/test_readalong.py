import pytest
from pymarc import Field

from scripts.readalong import change_to_je


@pytest.mark.parametrize(
    "arg,expectation",
    [
        (["a", "J", "a", "FIC", "a", "ADAMS"], "READALONG J-E ADAMS"),
        (["a", "J ", "a", " FIC ", "a", "ADAMS"], "READALONG J-E ADAMS"),
        (["a", "SPA", "a", "J", "a", "FIC", "a", "ADAMS"], "READALONG SPA J-E ADAMS"),
        (["a", "J-E", "a", "ADAMS"], "READALONG J-E ADAMS"),
    ],
)
def test_change_to_je(arg, expectation):
    subs = ["a", "READALONG"]
    subs.extend(arg)
    callNo = Field(tag="099", indicators=[" ", " "], subfields=subs)
    assert change_to_je(callNo).value() == expectation
