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
        Contains columns specified in `column_names` with coordinates of the
        weather data grid point locations. Columns with other column names are
        ignored.

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
