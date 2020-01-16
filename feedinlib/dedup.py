""" Deduplication tools

This module contains tools, mainly the single `deduplicate` function, to remove
duplicates from data.
"""
from itertools import filterfalse, tee
from numbers import Number
from typing import List, Tuple, Union

from pandas import Timestamp

TimeseriesEntry = Tuple[Timestamp, Timestamp, Union[str, Number]]


def runs(
    accumulator: List[List[Tuple[int, TimeseriesEntry]]],
    element: Tuple[int, TimeseriesEntry],
) -> List[List[Tuple[int, TimeseriesEntry]]]:
    (index, (start, stop, value)) = element
    last = accumulator[-1]
    if (not last) or ((start, stop) == tuple(last[-1][1][0:2])):
        last.append(element)
    else:
        accumulator.append([element])
    return accumulator


def partition(predicate, iterable):
    """ Use a predicate to partition entries into false and true ones.

    Taken from:

        https://docs.python.org/dev/library/itertools.html#itertools-recipes

    Examples
    --------
    >>> def is_odd(x): return x % 2 != 0
    ...
    >>> [list(t) for t in partition(is_odd, range(10))]
    [[0, 2, 4, 6, 8], [1, 3, 5, 7, 9]]
    """
    t1, t2 = tee(iterable)
    return filterfalse(predicate, t1), filter(predicate, t2)


# TODO: Figure out which of the above can be replaced by stuff from the
#       `more-itertools` package.


def deduplicate(
    timeseries: List[TimeseriesEntry],
    absolute_margin: float = 0.1,
    relative_margin: float = 0.1,
) -> List[TimeseriesEntry]:
    """ Remove duplicates from the supplied `timeseries`.

    Currently the deduplication relies on `timemseries` being formatted
    according to how data is stored in `Weather.series.values()`. The function
    removes duplicates if the start and stop timestamps of consecutive segments
    are equal and the values are either equal or, if they are numeric, if their
    differences are smaller than a certain margin of error.

    Parameters
    ----------
    timeseries : List[TimeseriesEntry]
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
    timeseries : List[TimeseriesEntry]
        A copy of the input data with duplicate values removed.

    Raises
    ------
    ValueError
        If the data contains duplicates outside of the allowed margins.
    """
    # TODO: Fix the data. If possible add a constraint preventing this from
    #       happending again alongside the fix.
    #       This is just here because there's duplicate data (that we know)
    #       at the end of 2017. The last timestamp of 2017 is duplicated in
    #       the first timespan of 2018. And unfortunately it's not exactly
    #       duplicated. The timestamps are equal, but the values are only
    #       equal within a certain margin.
    result = (
        timeseries[:-1]
        if (timeseries[k][-1][0:2] == self.series[k][-2][0:2])
        and (
            (timeseries[k][-1][2] == self.series[k][-2][2])
            or (
                isinstance(timeseries[k][-1][2], Number)
                and isinstance(timeseries[k][-2][2], Number)
                and (abs(timeseries[k][-1][2] - self.series[k][-2][2]) <= 0.5)
            )
        )
        else timeseries[k]
    )
    # TODO: Collect duplication errors not cought by the code above.
    return result
