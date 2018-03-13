import pandas as pd
import xarray as xr
import numpy as np
import requests
import logging
import yaml
import json
import os
import hashlib
#import sqlalchemy

from datetime import datetime
from calendar import monthrange
#from opendap_download.multi_processing_download import DownloadManager
import math
from functools import partial
import re
import getpass
from datetime import datetime, timedelta
import dateutil.parser

# Set up a log
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('notebook')

BASE_URL = 'https://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/' \
           'M2T1NXSLV.5.12.4/'


# ToDo: Add check for southwestern and northeastern coordinate
def closest_coordinates(coordinates_sw, coordinates_ne):
    """
    The area/coordinates will be converted from lat/lon to the GEOS-5 MERRA-2
    grid coordinates. Since the resolution of the MERRA-2 grid is 0.5 x 0.625°,
    the given coordinates will be matched as close as possible.

    Parameters
    -----------
    coordinates_sw : :obj:`list` or :numpy:`array`
         List with latitude and longitude for southwestern coordinate of the
         rectangular area for which to download data. Format: [lat_sw, lon_sw].
    coordinates_ne : :obj:`list` or :numpy:`array`
         List with latitude and longitude for northeastern coordinate of the
         rectangular area for which to download data. Format: [lat_ne, lon_ne].

    Returns
    -------
    :numpy:`array`, :numpy:`array`
        Returns two arrays containing the closest GEOS-5 coordinates of the
        given coordinates for which weather data can be provided.
        Format: [lat_sw_geos, lon_sw_geos], [lat_ne_geos, lon_ne_geos]

    References
    -----------
    .. [1] Global Modeling and Assimilation Office: MERRA-2: File
           Specification, 2016,
           https://gmao.gsfc.nasa.gov/pubs/docs/Bosilovich785.pdf

    """

    def _convert_to_geos5(coords):
        """
        Convert coordinate to GEOS-5 MERRA-2 native grid coordinate

        Parameters
        -----------
        coords : :obj:`list` or :numpy:`array`
             List or array with latitude and longitude of one point.
             Format: [lat, lon].

        Returns
        -------
        :numpy:`array`
            Array with GEOS-5 native grid latitude and longitude of
            the given point. Format: [lat_geos, lon_geos].

        """
        return (np.array(coords) + [90, 180]) / [0.5, 0.625]

    def _convert_from_geos5(coords):
        """
        Convert coordinate from GEOS-5 MERRA-2 native grid coordinate

        Parameters
        -----------
        coords : :obj:`list` or :numpy:`array`
             List or array with GEOS-5 native grid latitude and longitude of
             one coordinate. Format: [lat_geos, lon_geos].

        Returns
        -------
        :numpy:`array`
            Array with latitude and longitude of the given point.
            Format: [lat, lon].

        """
        return -np.array([90, 180]) + np.array(coords) * [0.5, 0.625]

    def find_closest_coordinate(lat_lon, lat_lon_array):
        # ToDo: should find closest coordinate on a sphere
        """
        Find closest latitude/longitude to the given latitude/longitude
        weather data can be provided for.

        Parameters
        -----------
        lat_lon : :obj:`float`
            GEOS-5 latitude or longitude for which to find the closest
            latitude or longitude weather data can be provided for.
        lat_lon_array : :numpy:`array`
             Array containing all latitudes or longitudes of the GEOS-5
             native grid for which weather data can be provided.

        Returns
        -------
        :obj:`int`
            Closest GEOS-5 latitude or longitude weather data can be provided
            for.

        """
        # np.argmin() finds the smallest value in an array and returns its
        # index. np.abs() returns the absolute value of each item of an array.
        # To summarize, the function finds the difference closest to 0 and
        # returns its index.
        index = np.abs(lat_lon_array - lat_lon).argmin()
        return lat_lon_array[index]

    # Convert coordinates defining the area to GEOS-5 native grid coordinates
    coordinates_sw_geos5 = _convert_to_geos5(coordinates_sw)
    coordinates_ne_geos5 = _convert_to_geos5(coordinates_ne)

    # Set up arrays containing all latitudes and longitudes weather data can
    # be provided for
    lat_coords = np.arange(0, 361, dtype=int)
    lon_coords = np.arange(0, 576, dtype=int)

    # Find the closest coordinate in the GEOS-5 native grid weather data can
    # be provided for
    lat_sw_geos5_closest = find_closest_coordinate(
        coordinates_sw_geos5[0], lat_coords)
    lon_sw_geos5_closest = find_closest_coordinate(
        coordinates_sw_geos5[1], lon_coords)
    coordinates_sw_geos5_closest = [lat_sw_geos5_closest, lon_sw_geos5_closest]
    lat_ne_geos5_closest = find_closest_coordinate(
        coordinates_ne_geos5[0], lat_coords)
    lon_ne_geos5_closest = find_closest_coordinate(
        coordinates_ne_geos5[1], lon_coords)
    coordinates_ne_geos5_closest = [lat_ne_geos5_closest, lon_ne_geos5_closest]

    # Check the precision of the grid coordinates
    coordinates_sw_closest = _convert_from_geos5(coordinates_sw_geos5_closest)
    coordinates_ne_closest = _convert_from_geos5(coordinates_ne_geos5_closest)
    log.info('Closest coordinates for southwestern point: [{}, {}]'.format(
        coordinates_sw_closest[0], coordinates_sw_closest[1]))
    log.info('Closest coordinates for northeastern point: [{}, {}]'.format(
        coordinates_ne_closest[0], coordinates_ne_closest[1]))

    return coordinates_sw_geos5_closest, coordinates_ne_geos5_closest


def translate_year_to_file_number(year):
    """
    Returns a file number corresponding to the specified year.

    MERRA-2 file names consist of a number and a meta data string. The number
    changes over the years, e.g. 1980 until 1991 it is 100, 1992 until 2000 it
    is 200, etc.

    Parameters
    -----------
    year : :obj:`int`
        Year for which to obtain the weather data

    Returns
    --------
    :obj:`str`
        File number corresponding to the specified year.

    """
    if 1980 <= year < 1992:
        file_number = '100'
    elif 1992 <= year < 2001:
        file_number = '200'
    elif 2001 <= year < 2011:
        file_number = '300'
    elif year >= 2011:
        file_number = '400'
    else:
        raise Exception('The specified year is out of range.')

    return file_number





def generate_download_links(download_years, base_url, dataset_name, url_params):

    """
    Generates the links for the download.
    download_years: The years you want to download as array.
    dataset_name: The name of the data set. For example tavg1_2d_slv_Nx

    Parameters
    ----------
    :numpy:`array`, :numpy:`array`
        Returns two arrays containing the closest GEOS-5 coordinates of the
        given coordinates for which weather data can be provided.
        Format: [lat_sw_geos, lon_sw_geos], [lat_ne_geos, lon_ne_geos]
    """
    urls = []
    for y in download_years:
        # build the file_number
        y_str = str(y)
        file_num = translate_year_to_file_number(download_year)
        for m in range(1, 13):
            # build the month string: for the month 1 - 9 it starts with a leading 0.
            # zfill solves that problem
            m_str = str(m).zfill(2)
            # monthrange returns the first weekday and the number of days in a
            # month. Also works for leap years.
            _, nr_of_days = monthrange(y, m)
            for d in range(1, nr_of_days + 1):
                d_str = str(d).zfill(2)
                # Create the file name string
                file_name = 'MERRA2_{num}.{name}.{y}{m}{d}.nc4'.format(
                    num=file_num, name=dataset_name,
                    y=y_str, m=m_str, d=d_str)
                # Create the query
                query = '{base}{y}/{m}/{name}.nc4?{params}'.format(
                    base=base_url, y=y_str, m=m_str,
                    name=file_name, params=url_params)
                urls.append(query)
    return urls


def generate_download_link(coordinates_sw_geos5, coordinates_ne_geos5,
                           requested_params, year):
    """


    Parameters
    ----------
    coordinates_sw_geos5 : :numpy:`array`
        GEOS-5 coordinates of the southwestern point.
        Format: [lat_geos, lon_geos]
    coordinates_ne_geos5 : :numpy:`array`
        GEOS-5 coordinates of the northeastern point.
        Format: [lat_geos, lon_geos]
    requested_params : :numpy:`array`

    """

    # Creates a string that looks like [start:1:end]. start and end are the lat or
    # lon coordinates define your area.
    requested_lat = '[{lat_1}:1:{lat_2}]'.format(
        lat_1=coordinates_sw_geos5[0], lat_2=coordinates_ne_geos5[0])
    requested_lon = '[{lon_1}:1:{lon_2}]'.format(
        lon_1=coordinates_sw_geos5[1], lon_2=coordinates_ne_geos5[1])

    # Creates a string containing all the parameters in query form
    parameter = map(lambda x: x + '[0:1:23]', requested_params)
    parameter = map(lambda x: x + requested_lat, parameter)
    parameter = map(lambda x: x + requested_lon, parameter)

    parameter = ','.join(parameter)


    generated_URL = generate_download_links([year], BASE_URL,
                                            'tavg1_2d_slv_Nx',
                                            parameter)

    # See what a query to the MERRA-2 portal looks like.
    log.info(generated_URL[0])



# ToDo: auch einzelne Tage oder Monate zulassen
def main(year, coordinates_sw, coordinates_ne):
    """
    Main function to download MERRA-2 weather data.

    The user has to provide a year and two corner coordinates of a rectangular
    area (Format WGS84, decimal system).

    Parameters
    -----------
    year : :obj:`int`
        Year for which to obtain the weather data
    coordinates_sw : :obj:`list`
         List with latitude and longitude for southwestern coordinate of the
         rectangular area for which to download data. Format: [lat_sw, lon_sw].
    coordinates_ne : :obj:`list`
         List with latitude and longitude for northeastern coordinate of the
         rectangular area for which to download data. Format: [lat_ne, lon_ne].


    """
    # User input of timespan
    download_year = year

    # Create the start date 2016-01-01
    download_start_date = str(download_year) + '-01-01'

    # get MERRA coordinates
    coordinates_sw_geos5_closest, coordinates_ne_geos5_closest = \
        closest_coordinates(coordinates_sw, coordinates_ne)

    requested_params = ['U2M', 'U10M', 'U50M', 'V2M', 'V10M', 'V50M', 'DISPH']
    generate_download_link(coordinates_sw_geos5_closest, coordinates_ne_geos5_closest,
                           requested_params, download_year)


main(2016, [3.9049, 116.6090], [21.7830, 126.9596])


#
#     # Download data (one file per day and dataset) with links to local directory.
#     # Username and password for MERRA-2 (NASA earthdata portal)
#     username = input('Username: ')
#     password = getpass.getpass('Password:')
#
#     # The DownloadManager is able to download files. If you have a fast internet
#     # connection, setting this to 2 is enough. If you have slow wifi, try setting
#     # it to 4 or 5. If you download too fast, the data portal might ban you for a
#     # day.
#     NUMBER_OF_CONNECTIONS = 5
#
#     # The DownloadManager class is defined in the opendap_download module.
#     download_manager = DownloadManager()
#     download_manager.set_username_and_password(username, password)
#     download_manager.download_path = 'download_wind'
#     download_manager.download_urls = generated_URL
#
#     # If you want to see the download progress, check the download folder you
#     # specified
#     %time download_manager.start_download(NUMBER_OF_CONNECTIONS)
#
#     # Download time approx. 20+ min.
#
#
#
#
#     # Roughness data is in a different data set. The parameter is called Z0M.
#     roughness_para = generate_url_params(['Z0M'], requested_time,
#                                          requested_lat, requested_lon)
#     ROUGHNESS_BASE_URL = 'https://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXFLX.5.12.4/'
#     roughness_links = generate_download_links([download_year], ROUGHNESS_BASE_URL,
#                                               'tavg1_2d_flx_Nx', roughness_para)
#
#     download_manager.download_path = 'download_roughness'
#     download_manager.download_urls = roughness_links
#
#     # If you want to see the download progress, check the download folder you
#     # specified.
#     %time download_manager.start_download(NUMBER_OF_CONNECTIONS)
#
#     # Download time approx. 12+ min.
#
#
#
#
#     # Parameters SWGDN and SWTDN
#     radiation_para = generate_url_params(['SWGDN', 'SWTDN'], requested_time,
#                                          requested_lat, requested_lon)
#     RADIATION_BASE_URL = 'https://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXRAD.5.12.4/'
#     radiation_links = generate_download_links([download_year], RADIATION_BASE_URL,
#                                              'tavg1_2d_rad_Nx', radiation_para)
#
#     download_manager.download_path = 'download_radiation'
#     download_manager.download_urls = radiation_links
#
#     %time download_manager.start_download(NUMBER_OF_CONNECTIONS)
#
#     # Download time approx. 8+ min.
#
#
#
#
#     # Parameter T2M (i.e. the temperature 2 meters above displacement height)
#     temperature_para = generate_url_params(['T2M'], requested_time,
#                                          requested_lat, requested_lon)
#     TEMPERATURE_BASE_URL = 'http://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/'
#     temperature_links = generate_download_links([download_year], TEMPERATURE_BASE_URL,
#                                              'tavg1_2d_slv_Nx', temperature_para)
#
#     download_manager.download_path = 'download_temperature'
#     download_manager.download_urls = temperature_links
#
#     %time download_manager.start_download(NUMBER_OF_CONNECTIONS)
#
#     # Download time approx. 13+ min.
#
#
#
#
#     # Parameter RHOA
#     density_para = generate_url_params(['RHOA'], requested_time,
#                                          requested_lat, requested_lon)
#     DENSITY_BASE_URL = 'http://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXFLX.5.12.4/'
#     density_links = generate_download_links([download_year], DENSITY_BASE_URL,
#                                              'tavg1_2d_flx_Nx', density_para)
#
#     download_manager.download_path = 'download_density'
#     download_manager.download_urls = density_links
#
#     %time download_manager.start_download(NUMBER_OF_CONNECTIONS)
#
#     # Download time approx. 13+ min.
#
#
#
#
#     # Parameters PS
#     pressure_para = generate_url_params(['PS'], requested_time,
#                                          requested_lat, requested_lon)
#     PRESSURE_BASE_URL = 'http://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/'
#     pressure_links = generate_download_links([download_year], PRESSURE_BASE_URL,
#                                              'tavg1_2d_slv_Nx', pressure_para)
#
#     download_manager.download_path = 'download_pressure'
#     download_manager.download_urls = pressure_links
#
#     %time download_manager.start_download(NUMBER_OF_CONNECTIONS)
#
#     # Download time approx. 15+ min.


# def download_dimensions():
#     # The dimensions map the MERRA2 grid coordinates to lat/lon. The coordinates
#     # to request are 0:360 wheare as the other coordinates are 1:361
#     requested_lat_dim = '[{lat_1}:1:{lat_2}]'.format(
#                         lat_1=lat_co_1_closest, lat_2=lat_co_2_closest)
#     requested_lon_dim = '[{lon_1}:1:{lon_2}]'.format(
#                         lon_1=lon_co_1_closest , lon_2=lon_co_2_closest )
#
#     lat_lon_dimension_para = 'lat' + requested_lat_dim + ',lon' + requested_lon_dim
#
#     # Creating the download url.
#     dimension_url = 'https://goldsmr4.sci.gsfc.nasa.gov/opendap/MERRA2/M2T1NXSLV.5.12.4/2014/01/MERRA2_400.tavg1_2d_slv_Nx.20140101.nc4.nc4?'
#     dimension_url = dimension_url + lat_lon_dimension_para
#     download_manager.download_path = 'dimension_scale'
#     download_manager.download_urls = [dimension_url]
#
#     # Since the dimension is only one file, we only need one connection.
#     %time download_manager.start_download(1)
#
#
#
#
#     file_path = os.path.join('dimension_scale', DownloadManager.get_filename(
#             dimension_url))
#
#     with xr.open_dataset(file_path) as ds_dim:
#         df_dim = ds_dim.to_dataframe()
#
#     lat_array = ds_dim['lat'].data.tolist()
#     lon_array = ds_dim['lon'].data.tolist()
#
#     # The log output helps evaluating the precision of the received data.
#     log.info('Requested lat: ' + str((lat_1, lat_2)))
#     log.info('Received lat: ' + str(lat_array))
#     log.info('Requested lon: ' + str((lon_1, lon_2)))
#     log.info('Received lon: ' + str(lon_array))


def extract_date(data_set):
    """
    Extracts the date from the filename before merging the datasets.
    """
    try:
        # The attribute name changed during the development of this script
        # from HDF5_Global.Filename to Filename.
        if 'HDF5_GLOBAL.Filename' in data_set.attrs:
            f_name = data_set.attrs['HDF5_GLOBAL.Filename']
        elif 'Filename' in data_set.attrs:
            f_name = data_set.attrs['Filename']
        else:
            raise AttributeError('The attribute name has changed again!')

        # find a match between "." and ".nc4" that does not have "." .
        exp = r'(?<=\.)[^\.]*(?=\.nc4)'
        res = re.search(exp, f_name).group(0)
        # Extract the date.
        y, m, d = res[0:4], res[4:6], res[6:8]
        date_str = ('%s-%s-%s' % (y, m, d))
        data_set = data_set.assign(date=date_str)
        return data_set

    except KeyError:
        # The last dataset is the one all the other sets will be merged into.
        # Therefore, no date can be extracted.
        return data_set


def convert_to_dataframe():
    file_path = os.path.join('download_wind', '*.nc4')

    try:
        with xr.open_mfdataset(file_path, concat_dim='date',
                               preprocess=extract_date) as ds_wind:
            print(ds_wind)
            df_wind = ds_wind.to_dataframe()

    except xr.MergeError as e:
        print(e)




    df_wind.reset_index(inplace=True)



    start_date = datetime.strptime(download_start_date, '%Y-%m-%d')

    def calculate_datetime(d_frame):
        """
        Calculates the accumulated hour based on the date.
        """
        cur_date = datetime.strptime(d_frame['date'], '%Y-%m-%d')
        hour = int(d_frame['time'])
        delta = abs(cur_date - start_date).days
        date_time_value = (delta * 24) + (hour)
        return date_time_value


    df_wind['date_time_hours'] = df_wind.apply(calculate_datetime, axis=1)
    df_wind




# def converting_timeformat_to_ISO8601(row):
#     """Generates datetime according to ISO 8601 (UTC)"""
#     date = dateutil.parser.parse(row['date'])
#     hour = int(row['time'])
#     # timedelta from the datetime module enables the programmer
#     # to add time to a date.
#     date_time = date + timedelta(hours = hour)
#     return str(date_time.isoformat()) + 'Z'  # MERRA2 datasets have UTC time zone.
# df_wind['date_utc'] = df_wind.apply(converting_timeformat_to_ISO8601, axis=1)
#
# df_wind['date_utc']
#
# # execution time approx. 3+ min



def calculate_windspeed(d_frame, idx_u, idx_v):
    """
    Calculates the windspeed. The returned unit is m/s
    """
    um = float(d_frame[idx_u])
    vm = float(d_frame[idx_v])
    speed = math.sqrt((um ** 2) + (vm ** 2))
    return round(speed, 2)

# # partial is used to create a function with pre-set arguments.
# calc_windspeed_2m = partial(calculate_windspeed, idx_u='U2M', idx_v='V2M')
# calc_windspeed_10m = partial(calculate_windspeed, idx_u='U10M', idx_v='V10M')
# calc_windspeed_50m = partial(calculate_windspeed, idx_u='U50M', idx_v='V50M')
#
# df_wind['v_2m'] = df_wind.apply(calc_windspeed_2m, axis=1)
# df_wind['v_10m']= df_wind.apply(calc_windspeed_10m, axis=1)
# df_wind['v_50m'] = df_wind.apply(calc_windspeed_50m, axis=1)
# df_wind
#
# # execution time approx. 3 min
#
#
#
#
#
# file_path = os.path.join('download_roughness', '*.nc4')
# with xr.open_mfdataset(file_path, concat_dim='date',
#                        preprocess=extract_date) as ds_rough:
#     df_rough = ds_rough.to_dataframe()
#
# df_rough.reset_index(inplace=True)
#
#
#
# file_path = os.path.join('download_radiation', '*.nc4')
# try:
#     with xr.open_mfdataset(file_path, concat_dim='date',
#                            preprocess=extract_date) as ds_rad:
#         print(ds_rad)
#         df_rad = ds_rad.to_dataframe()
#
# except xr.MergeError as e:
#     print(e)
# df_rad.reset_index(inplace=True)
#
#
#
#
# file_path = os.path.join('download_temperature', '*.nc4')
# try:
#     with xr.open_mfdataset(file_path, concat_dim='date',
#                            preprocess=extract_date) as ds_temp:
#         print(ds_temp)
#         df_temp = ds_temp.to_dataframe()
#
# except xr.MergeError as e:
#     print(e)
# df_temp.reset_index(inplace=True)
#
#
#
#
# file_path = os.path.join('download_density', '*.nc4')
# try:
#     with xr.open_mfdataset(file_path, concat_dim='date',
#                            preprocess=extract_date) as ds_dens:
#         print(ds_dens)
#         df_dens = ds_dens.to_dataframe()
#
# except xr.MergeError as e:
#     print(e)
# df_dens.reset_index(inplace=True)
#
#
#
#
# file_path = os.path.join('download_pressure', '*.nc4')
# try:
#     with xr.open_mfdataset(file_path, concat_dim='date',
#                            preprocess=extract_date) as ds_pres:
#         print(ds_pres)
#         df_pres = ds_pres.to_dataframe()
#
# except xr.MergeError as e:
#     print(e)
# df_pres.reset_index(inplace=True)
#
#
#
#
# df = pd.merge(df_wind, df_rough, on=['date', 'lat', 'lon', 'time'])
# df = pd.merge(df, df_rad, on=['date', 'lat', 'lon', 'time'])
# df = pd.merge(df, df_temp, on=['date', 'lat', 'lon', 'time'])
# df = pd.merge(df, df_dens, on=['date', 'lat', 'lon', 'time'])
# df = pd.merge(df, df_pres, on=['date', 'lat', 'lon', 'time'])
# df.info()
#
#
#
# # Calculate height for h1 (displacement height +2m) and h2 (displacement height
# # +10m).
# df['h1'] = df.apply((lambda x:int(x['DISPH']) + 2), axis=1)
# df['h2'] = df.apply((lambda x:int(x['DISPH']) + 10), axis=1)
#
#
#
#
# df.drop('DISPH', axis=1, inplace=True)
# df.drop(['time', 'date'], axis=1, inplace=True)
# df.drop(['U2M', 'U10M', 'U50M', 'V2M', 'V10M', 'V50M'], axis=1, inplace=True)
#
# df['lat'] = df['lat'].apply(lambda x: lat_array[int(x)])
# df['lon'] = df['lon'].apply(lambda x: lon_array[int(x)])
#
#
#
# rename_map = {'date_time_hours': 'cumulated hours',
#               'date_utc': 'timestamp',
#               'v_2m': 'v1',
#               'v_10m': 'v2',
#               'Z0M': 'z0',
#               'T2M': 'T',
#               'RHOA': 'rho',
#               'PS': 'p'
#              }
#
# df.rename(columns=rename_map, inplace=True)
#
#
#
#
# # Change order of the columns
# columns = ['timestamp', 'cumulated hours', 'lat', 'lon',
#         'v1', 'v2', 'v_50m',
#         'h1', 'h2', 'z0', 'SWTDN', 'SWGDN', 'T', 'rho', 'p']
# df = df[columns]
#
#
#
# df.to_csv('weather_data_Nome_2015.csv', index=False)
# df.to_pickle('weather_data_Nome_2015.pkl')