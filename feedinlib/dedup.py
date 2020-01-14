""" Deduplication tools

This module contains tools, mainly the single `deduplicate` function, to remove
duplicates from data.
"""
from numbers import Number
from typing import List, Union

from pandas import Timestamp


def deduplicate(
    timeseries: List((Timestamp, Timestamp, Union[str, Number])),
    absolute_margin: float = 0.1,
    relative_margin: float = 0.1,
):
    """ Remove duplicates from the supplied `timeseries`.

    Currently the deduplication relies on `timemseries` being formatted
    according to how data is stored in `Weather.series.values()`. The function
    removes duplicates if the start and stop timestamps of consecutive segments
    are equal and the values are either equal or, if they are numeric, if their
    differences are smaller than a certain margin of error.

    Parameters
    ----------
    timeseries : List((Timestamp, Timestamp, Union[str, Number]))
        The timeseries to duplicate.
    absolute_margin : float
        The absolute value of the difference between the two values has to be
        smaller than or equal to this.
    relative_margin : float
        The absolute value of the difference between the two values has to be
        smaller than or equal to this, when interpreted as a percentage of the
        maximum of the absolute values of the two compared values.

    Returns
    -------
    timeseries : List((Timestamp, Timestamp, Union[str, Number]))
        A copy of the input data with duplicate values removed.

    Raises
    ------
    ValueError
        If the data contains duplicates outside of the allowed margins.
    """

    return timeseries
