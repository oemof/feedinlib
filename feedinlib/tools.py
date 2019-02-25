import pandas as pd
from scipy.spatial import cKDTree
import numpy as np


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
    register : pd.DataFrame
        Input `register` data frame containing additionally the locations of
        the closest weather data grid points in 'weather_lat' (latitude of
        weather location) and 'weather_lon' (longitude of weather location).

    """
    if register[['lat', 'lon']].isnull().values.any():
        raise ValueError("Missing coordinates in power plant register.")
    closest_coordinates =  get_closest_coordinates(
        weather_coordinates, register[['lat', 'lon']]).set_index(
        register.index)
    register[['weather_lat', 'weather_lon']] = closest_coordinates
    return register

