import pandas as pd
from scipy.spatial import cKDTree
import numpy as np
import logging


def return_unique_pairs(df, column_names):
    r"""
    Returns all unique pairs of values of DataFrame `df`.

    Returns
    -------
    pd.DataFrame
        Columns (`column_names`) contain unique pairs of values.

    """
    return df.groupby(column_names).size().reset_index().drop([0], axis=1)


def get_closest_coordinates(weather_coordinates, pp_locations,
                            column_names=['lat', 'lon']):
    r"""
    Finds the coordinates in a data frame that are closest to `pp_locations`.

    Parameters
    ----------
    weather_coordinates : pd.DataFrame
        Contains columns specified in `column_names` with coordinates of the
        weather data grid point locations. Columns with other column names are
        ignored.
    pp_locations : List or pd.DataFrame
        Location(s) of power plant(s) as pd.DataFrame (['lat, 'lon']) or as
        list for one power plant ([lat, lon]).
    column_names : List
        List of column names in which the coordinates of `weather_coordinates`
        are located. Default: '['lat', 'lon']'.

    Returns
    -------
    pd.Series
        Contains closest coordinates with `column_names` as indices.

    """
    coordinates_df = return_unique_pairs(weather_coordinates, column_names)
    tree = cKDTree(coordinates_df)
    dists, index = tree.query(np.asarray(pp_locations), k=1)
    return coordinates_df.iloc[index]


def add_weather_locations_to_register(register, weather_coordinates):
    r"""
    Parameters
    ------------
    register : pd.DataFrame
        Contains location of each power plant in columns 'lat' (latitude) and
        'lon' (longitude).
    weather_coordinates : pd.DataFrame
        Contains coordinates of the weather data grid point locations in
        columns/multi index named 'lat' and 'lon'. Columns with other column
        names are ignored.

    Returns
    -------
    register : gpd.GeoDataFrame
        Input `register` data frame containing additionally the locations of
        the closest weather data grid points in 'weather_lat' (latitude of
        weather location) and 'weather_lon' (longitude of weather location).

    """
    if register[['lat', 'lon']].isnull().values.any():
        logging.warning("Missing coordinates in power plant register are "
                        "dropped.")
        register = register[np.isfinite(register['lon'])]
        register = register[np.isfinite(register['lat'])]
    closest_coordinates =  get_closest_coordinates(
        weather_coordinates, register[['lat', 'lon']]).set_index(
        register.index)
    register = register.assign(weather_lat=closest_coordinates['lat'].values,
                    weather_lon=closest_coordinates['lon'].values)

    return register


def example_weather_wind(filename): # todo: to be deleted. Is used in region.py
    # loading weather data
    try:
        weather_df = pd.read_csv(filename,
                                 header=[0, 1], index_col=[0, 1, 2],
                                 parse_dates=True)
    except FileNotFoundError:
        raise FileNotFoundError("Please adjust the filename incl. path.")
    # change type of height from str to int by resetting columns
    l0 = [_[0] for _ in weather_df.columns]
    l1 = [int(_[1]) for _ in weather_df.columns]
    weather_df.columns = [l0, l1]
    return weather_df


def get_time_periods_with_equal_capacity(register, start=None, stop=None):
    r"""

    Parameters:
    -----------
    register : pd.DataFrame
        Contains commissioning dates'(TimeStamp) in column 'commissioning_date' and
        decommissioning dates in 'decommissioning_date'.
    start : int or str (or pd.DatetimeIndex?)
        Specifies the year (int) or date (str) from which the periods of equal
        capacities are fetched.
    stop : int or str (or pd.DatetimeIndex?)
        Specifies the year (int) or date (str) up to which the periods of equal
        capacities are fetched. If stop is an integer the whole year is
        fetched.

    Returns
    -------
    periods : pd.DataFrame
        Start dates (column 'start') and end dates (column 'end) of periods
        with constant capacity.

    todo: check edges of periods and raise errors z.B. time stamp
    """
    if isinstance(start, int):
        start = '{}-01-01 00:00:00'.format(start)
    if isinstance(stop, int):
        stop = '{}-12-31 23:59:59'.format(stop)
    # find dates with capacity change within start and stop
    dates = register['commissioning_date']
    dates = dates.append(register['decommissioning_date']).dropna().unique()
    # add time zone to start and stop
    if stop.tz is None:
        stop = stop.tz_localize(dates.tz)
    if start.tz is None:
        start = start.tz_localize(dates.tz)
    dates_filtered = pd.Series(dates[(dates >= start) & (dates <= stop)])
    # build data frame with periods with constant capacity
    start_dates = dates_filtered.append(pd.Series(start)).sort_values()
    start_dates.index = np.arange(0, len(start_dates))
    stop_dates = dates_filtered.append(pd.Series(stop)).sort_values()
    stop_dates.index = np.arange(0, len(stop_dates))
    periods = pd.DataFrame({'start': start_dates,'stop': stop_dates})
    # to datetime
    periods['start'] = pd.to_datetime(periods['start'], utc=True)
    periods['stop'] = pd.to_datetime(periods['stop'], utc=True)
    return periods


def filter_register_by_period(register, start, stop):
    r"""
    Filter register by period.

    Parameters:
    -----------
    register : pd.DataFrame
        Contains commissioning dates in column 'commissioning_date' and
        decommissioning dates in 'decommissioning_date'. Make sure there are
        no missing values!
    start : int or str (or pd.DatetimeIndex?)
        Start of period. Power plants decommissioned before this date are
        neglected.
    stop : int or str (or pd.DatetimeIndex?)
        End of period. Power plants installed from this date are neglected.

    """
    if not isinstance(register['commissioning_date'].iloc[0], pd.Timestamp):
        register['commissioning_date'] = pd.to_datetime(
            register['commissioning_date'], utc=True)
    if not isinstance(register['decommissioning_date'].iloc[0], pd.Timestamp):
        register['decommissioning_date'] = pd.to_datetime(
            register['decommissioning_date'], utc=True)
    df_1 = register[register['decommissioning_date'] > start]
    filtered_register = df_1[df_1['commissioning_date'] < stop]
    return filtered_register