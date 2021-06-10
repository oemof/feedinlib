import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from feedinlib.cds_request_tools import get_cds_data_from_datespan_and_position


def get_era5_data_from_datespan_and_position(
    start_date,
    end_date,
    variable="feedinlib",
    latitude=None,
    longitude=None,
    grid=None,
    target_file=None,
    chunks=None,
    cds_client=None,
):
    """
    Send request for era5 data to the Climate Data Store (CDS)

    :param variable: (str or list of str) ERA5 variables to download. If you
        want to download all variables necessary to use the pvlib, set
        `variable` to 'pvlib'. If you want to download all variables necessary
        to use the windpowerlib, set `variable` to 'windpowerlib'. To download
        both variable sets for pvlib and windpowerlib, set `variable` to
        'feedinlib'.
    :param start_date: (str) start date of the date span in YYYY-MM-DD format
    :param end_date: (str) end date of the date span in YYYY-MM-DD format
    :param latitude: (number) latitude in the range [-90, 90] relative to the
        equator, north corresponds to positive latitude.
    :param longitude: (number) longitude in the range [-180, 180] relative to
        Greenwich Meridian, east relative to the meridian corresponds to
        positive longitude.
    :param grid: (list of float) provide the latitude and longitude grid
        resolutions in deg. It needs to be an integer fraction of 90 deg.
    :param target_file: (str) name of the file in which to store downloaded
        data locally
    :param chunks: (dict)
    :param cds_client: handle to CDS client (if none is provided, then it is
        created)
    :return: CDS data in an xarray format

    """
    if variable == "pvlib":
        variable = ["fdir", "ssrd", "2t", "10u", "10v"]
    elif variable == "windpowerlib":
        variable = ["100u", "100v", "10u", "10v", "2t", "fsr", "sp"]
    elif variable == "feedinlib":
        variable = [
            "100u",
            "100v",
            "fsr",
            "sp",
            "fdir",
            "ssrd",
            "2t",
            "10u",
            "10v",
        ]
    return get_cds_data_from_datespan_and_position(**locals())


def format_windpowerlib(ds):
    """
    Format dataset to dataframe as required by the windpowerlib's ModelChain.

    The windpowerlib's ModelChain requires a weather DataFrame with time
    series for

    - wind speed `wind_speed` in m/s,
    - temperature `temperature` in K,
    - roughness length `roughness_length` in m,
    - pressure `pressure` in Pa.

    The columns of the DataFrame need to be a MultiIndex where the first level
    contains the variable name as string (e.g. 'wind_speed') and the second
    level contains the height as integer in m at which it applies (e.g. 10,
    if it was measured at a height of 10 m).

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset with ERA5 weather data.

    Returns
    --------
    pd.DataFrame
        Dataframe formatted for the windpowerlib.

    """

    # compute the norm of the wind speed
    ds["wnd100m"] = np.sqrt(ds["u100"] ** 2 + ds["v100"] ** 2).assign_attrs(
        units=ds["u100"].attrs["units"], long_name="100 metre wind speed"
    )

    ds["wnd10m"] = np.sqrt(ds["u10"] ** 2 + ds["v10"] ** 2).assign_attrs(
        units=ds["u10"].attrs["units"], long_name="10 metre wind speed"
    )

    # drop not needed variables
    windpowerlib_vars = ["wnd10m", "wnd100m", "sp", "t2m", "fsr"]
    ds_vars = list(ds.variables)
    drop_vars = [
        _
        for _ in ds_vars
        if _ not in windpowerlib_vars + ["latitude", "longitude", "time"]
    ]
    ds = ds.drop(drop_vars)

    # convert to dataframe
    df = ds.to_dataframe().reset_index()

    # the time stamp given by ERA5 for mean values (probably) corresponds to
    # the end of the valid time interval; the following sets the time stamp
    # to the middle of the valid time interval
    df['time'] = df.time - pd.Timedelta(minutes=60)

    df.set_index(['time', 'latitude', 'longitude'], inplace=True)
    df.sort_index(inplace=True)
    df = df.tz_localize("UTC", level=0)

    # reorder the columns of the dataframe
    df = df[windpowerlib_vars]

    # define a multiindexing on the columns
    midx = pd.MultiIndex(
        levels=[
            ["wind_speed", "pressure", "temperature", "roughness_length"],
            # variable
            [0, 2, 10, 100],  # height
        ],
        codes=[
            [0, 0, 1, 2, 3],  # indexes from variable list above
            [2, 3, 0, 1, 0],  # indexes from the height list above
        ],
        names=["variable", "height"],  # name of the levels
    )

    df.columns = midx
    df.dropna(inplace=True)

    return df


def format_pvlib(ds):
    """
    Format dataset to dataframe as required by the pvlib's ModelChain.

    The pvlib's ModelChain requires a weather DataFrame with time series for

    - wind speed `wind_speed` in m/s,
    - temperature `temp_air` in C,
    - direct irradiation 'dni' in W/m² (calculated later),
    - global horizontal irradiation 'ghi' in W/m²,
    - diffuse horizontal irradiation 'dhi' in W/m²

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset with ERA5 weather data.

    Returns
    --------
    pd.DataFrame
        Dataframe formatted for the pvlib.

    """

    # compute the norm of the wind speed
    ds["wind_speed"] = np.sqrt(ds["u10"] ** 2 + ds["v10"] ** 2).assign_attrs(
        units=ds["u10"].attrs["units"], long_name="10 metre wind speed"
    )

    # convert temperature to Celsius (from Kelvin)
    ds["temp_air"] = ds.t2m - 273.15

    ds["dirhi"] = (ds.fdir / 3600.0).assign_attrs(units="W/m^2")
    ds["ghi"] = (ds.ssrd / 3600.0).assign_attrs(
        units="W/m^2", long_name="global horizontal irradiation"
    )
    ds["dhi"] = (ds.ghi - ds.dirhi).assign_attrs(
        units="W/m^2", long_name="direct irradiation"
    )

    # drop not needed variables
    pvlib_vars = ["ghi", "dhi", "wind_speed", "temp_air"]
    ds_vars = list(ds.variables)
    drop_vars = [
        _
        for _ in ds_vars
        if _ not in pvlib_vars + ["latitude", "longitude", "time"]
    ]
    ds = ds.drop(drop_vars)

    # convert to dataframe
    df = ds.to_dataframe().reset_index()

    # the time stamp given by ERA5 for mean values (probably) corresponds to
    # the end of the valid time interval; the following sets the time stamp
    # to the middle of the valid time interval
    df['time'] = df.time - pd.Timedelta(minutes=30)

    df.set_index(['time', 'latitude', 'longitude'], inplace=True)
    df.sort_index(inplace=True)
    df = df.tz_localize("UTC", level=0)

    df = df[["wind_speed", "temp_air", "ghi", "dhi"]]
    df.dropna(inplace=True)

    return df


def select_area(ds, lon, lat, g_step=0.25):
    """
    Select data for given location or rectangular area from dataset.

    In case data for a single location is requested, the nearest data point
    for which weather data is given is returned.

    Parameters
    -----------
    ds : xarray.Dataset
        Dataset with ERA5 weather data.
    lon : float or tuple
        Longitude of single location or area to select data for. In case
        longitude is provided as tuple first entry must be the west boundary
        and second entry the east boundary.
    lat : float or tuple
        Latitude of single location or area to select data for. In case
        latitude is provided as tuple first entry must be the south boundary
        and second entry the north boundary.
    g_step : float
        Grid resolution of weather data, needed to find nearest point in case
        a single location is requested.

    Returns
    -------
    xarray.Dataset
        Dataset containing selection for specified location or area.

    """
    select_point = True
    if np.size(lon) > 1:
        select_point = False
        lon_w, lon_e = lon
    else:
        lon_w = lon
        lon_e = lon + g_step

    if np.size(lat) > 1:
        select_point = False
        lat_s, lat_n = lat
    else:
        lat_s = lat
        lat_n = lat + g_step

    if select_point is True:
        answer = ds.sel(latitude=lat, longitude=lon, method="nearest")
    else:
        answer = ds.where(
            (lat_s < ds.latitude)
            & (ds.latitude <= lat_n)
            & (lon_w < ds.longitude)
            & (ds.longitude <= lon_e)
        )

    return answer


def select_geometry(ds, area):
    """
    Select data for given geometry from dataset.

    Parameters
    -----------
    ds : xarray.Dataset
        Dataset with ERA5 weather data.
    area : shapely's compatible geometry object (i.e. Polygon, Multipolygon, etc...)
        Area to select data for.

    Returns
    -------
    xarray.Dataset
        Dataset containing selection for specified location or area.

    """
    geometry = []
    lon_vals = []
    lat_vals = []

    df = pd.DataFrame([], columns=["lon", "lat"])

    for i, x in enumerate(ds.longitude):
        for j, y in enumerate(ds.latitude):
            lon_vals.append(x.values)
            lat_vals.append(y.values)
            geometry.append(Point(x, y))

    df["lon"] = lon_vals
    df["lat"] = lat_vals

    # create a geopandas to use the geometry functions
    crs = {"init": "epsg:4326"}
    geo_df = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)

    inside_points = geo_df.within(area)
    # if no points lie within area, return None
    if not inside_points.any():
        return None

    inside_lon = geo_df.loc[inside_points, "lon"].values
    inside_lat = geo_df.loc[inside_points, "lat"].values

    # prepare a list where the latitude and longitude of the points inside are
    # formatted as xarray of bools
    logical_list = []
    for lon, lat in zip(inside_lon, inside_lat):
        logical_list.append(
            np.logical_and((ds.longitude == lon), (ds.latitude == lat))
        )

    # bind all conditions from the list
    cond = np.logical_or(*logical_list[:2])
    for new_cond in logical_list[2:]:
        cond = np.logical_or(cond, new_cond)

    # apply the condition to where
    return ds.where(cond)


def weather_df_from_era5(
    era5_netcdf_filename, lib, start=None, end=None, area=None
):
    """
    Gets ERA5 weather data from netcdf file and converts it to a pandas
    dataframe as required by the spcified lib.

    Parameters
    -----------
    era5_netcdf_filename : str
        Filename including path of netcdf file containing ERA5 weather data
        for specified time span and area.
    start : None or anything `pandas.to_datetime` can convert to a timestamp
        Get weather data starting from this date. Defaults to None in which
        case start is set to first time step in the dataset.
    end : None or anything `pandas.to_datetime` can convert to a timestamp
        Get weather data upto this date. Defaults to None in which
        case the end date is set to the last time step in the dataset.
    area : shapely compatible geometry object (i.e. Polygon,  Multipolygon, etc...) or list(float) or list(tuple)
        Area specifies for which geographic area to return weather data. Area
        can either be a single location or an area.
        In case you want data for a single location provide a list in the
        form [lon, lat].
        If you want data for an area you can provide a shape of this area or
        specify a rectangular area giving a list of the
        form [(lon west, lon east), (lat south, lat north)].

    Returns
    -------
    pd.DataFrame
        Dataframe with ERA5 weather data in format required by the lib. In
        case a single location is provided in parameter `area` index of the
        dataframe is a datetime index. Otherwise the index is a multiindex
        with time, latitude and longitude levels.

    """
    ds = xr.open_dataset(era5_netcdf_filename)

    if area is not None:
        if isinstance(area, list):
            ds = select_area(ds, area[0], area[1])
        else:
            ds = select_geometry(ds, area)
            if ds is None:
                return pd.DataFrame()

    if lib == "windpowerlib":
        df = format_windpowerlib(ds)
    elif lib == "pvlib":
        df = format_pvlib(ds)
    else:
        raise ValueError(
            "Unknown value for `lib`. "
            "It must be either 'pvlib' or 'windpowerlib'."
        )

    # drop latitude and longitude from index in case a single location
    # is given in parameter `area`
    if area is not None and isinstance(area, list):
        if np.size(area[0]) == 1 and np.size(area[1]) == 1:
            df.index = df.index.droplevel(level=[1, 2])

    if start is None:
        start = df.index[0]
    if end is None:
        end = df.index[-1]
    return df[start:end]
