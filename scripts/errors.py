# -*- coding: utf-8 -*-

"""
overload.exceptions
~~~~~~~~~~~~~~~~~~~
This module contains the set of Overload's exceptions.
"""


class APITokenError(Exception):
    """Exception raised when Sierra API token is not obtained
    """

    pass


class APITokenExpiredError(Exception):
    """Exception raised when API access token appears to be expired
    """

    pass
