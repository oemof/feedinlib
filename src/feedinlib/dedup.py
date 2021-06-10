""" Deduplication tools

This module contains tools, mainly the single `deduplicate` function, to remove
duplicates from data.
"""
from functools import reduce
from itertools import filterfalse, tee
from pprint import pformat
from numbers import Number
from typing import Dict, List, Tuple, Union

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


def compress(
    multiples: List[Tuple[int, TimeseriesEntry]], margins: Dict[str, float],
) -> List[Tuple[slice, TimeseriesEntry]]:
    """ {}
    """.format(
        "Compresses equal timestamp runs if the values are inside "
        "the margin of error."
    )
    if not multiples:
        return multiples
    result = []
    index, (start, stop, value) = multiples[0]
    for ci, (start_, stop_, cv) in multiples[1:]:
        if not (
            (value == cv)
            or (
                isinstance(value, Number)
                and isinstance(cv, Number)
                and (abs(value - cv) <= margins["absolute"])
                and (
                    abs(value - cv) / max(abs(v) for v in [value, cv])
                    <= margins["relative"]
                )
            )
        ):
            result.append((slice(index, ci + 1), (start, stop, value)))
            index, value = ci, cv
    result.append((slice(index, multiples[-1][0] + 1), (start, stop, value)))
    return result


def deduplicate(
    timeseries: List[TimeseriesEntry], margins: Dict[str, float] = {},
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
    margins : Dict[str, float]
        The margins of error. Can contain one or both of the strings
        :code:`"absolute"` and :code:`"relative"` as keys with the numbers
        stored under these keys having the following meaning:

            - for :code:`absolute` value of the difference between the two
              values has to be smaller than or equal to this while
            - for :code:`relative` this difference has to be smaller than or
              equal to this when interpreted as a fraction of the maximum of
              the absolute values of the two compared values.

        By default these limits are set to be infinitely big.

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
    # TODO: Use [`unique_iter`][0] for unsafe removal, i.e. if both margins
    #       are infinite. Or find an alternative in [`more-itertools`][1].
    #       [0]: https://boltons.readthedocs.io/en/latest/iterutils.html#boltons.iterutils.unique_iter
    #       [1]: https://pypi.org/project/more-itertools/

    margins = {
        **{"absolute": float("inf"), "relative": float("inf")},
        **margins,
    }
    multiples = [
        run
        for run in reduce(runs, enumerate(timeseries), [[]])
        if len(run) > 1
    ]
    compressed = [compress(m, margins) for m in multiples]
    errors = [c for c in compressed if len(c) > 1]
    if errors:
        raise ValueError(
            "Found duplicate timestamps while retrieving data:\n{}".format(
                pformat(errors)
            )
        )
    compressed.reverse()
    result = timeseries.copy()
    for c in compressed:
        result[c[0][0]] = (c[0][1],)
    return result
