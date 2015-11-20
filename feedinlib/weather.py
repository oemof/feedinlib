# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 16:01:02 2015

@author: uwe
"""

import pandas as pd


class FeedinWeather:
    def __init__(self, **kwargs):
        r"""
        Class, containing all meta informations regarding the weather data set.

        Parameters
        ----------
        data : pandas.DataFrame, optional
            Containing the time series of the different parameters as columns
        timezone : string, optional
            Containing the name of the time zone using the naming of the
            IANA (Internet Assigned Numbers Authority) time zone database [40]_
        longitude : float, optional
            Longitude of the location of the weather data
        latitude : float, optional
            Latitude of the location of the weather data
        geometry : shapely.geometry object
            polygon or point representing the zone of the weather data
        data_height : dictionary, optional
            Containing the heights of the weather measurements or weather
            model in meters with the keys of the data parameter
        name : string
            Name of the weather data object

        Notes
        -----
        Depending on the used feedin modell some of the optional parameters
        might be mandatory.

        References
        ----------
        .. [40] `IANA time zone database <http://www.iana.org/time-zones>`_.

        """
        self.data = kwargs.get('data', None)
        try:
            self.timezone = self.data.index.tz
        except:
            self.timezone = kwargs.get('timezone', None)
        self.longitude = kwargs.get('longitude', None)
        self.latitude = kwargs.get('latitude', None)
        self.geometry = kwargs.get('geometry', None)
        self.data_height = kwargs.get('data_height', None)
        self.name = kwargs.get('name', None)

    def read_feedinlib_csv(self, filename, overwrite=True):
        r"""
        Reading a csv-file with a header containg the meta data of the time
        series.

        The header has to contain the time zone and has to end with a blank
        line. To add data of the data_height dictionary there should be space
        between the parameter name and the key name (e.g. # data_height
        v_wind: 10). Further more any number of parameters can be added.

        The file should have the following form:

        .. code::

            # timezone=
            # name: NAME
            # longitude: xx.xxx
            # latitude: yy.yyy
            # timezone: Continent/City
            # data_height temp_air: zz
            # data_height v_wind: vv

            ,temp_air,v_wind,.....
            2010-01-01 00:00:00+01:00,267.599,5.32697,...
            2010-01-01 01:00:00+01:00,267.596,5.46199,....
            ....

        Parameters
        ----------
        filename : string
            The filename with the full path and the suffix of the file.
        overwrite : boolean
            If False the only class attributes of NoneType will be overwritten
            with the data of the csv file. If True all class attributes will
            be overwriten with the data of the csv-file.

        Raises
        ------
        FileNotFoundError
            If the file defined by filename can not be found.
        """
        # Read meta data (location of weather data)
        meta_dict = {}
        skiprows = 0
        with open(filename, 'r') as f:
            while 1:
                tmp = f.readline()[2:-1]
                if not tmp.strip():
                    break
                tmp = tmp.replace(' ', '')
                [a, b] = tmp.split(':')
                meta_dict[a] = b
                skiprows += 1

        # Define attributes
        if self.latitude is None or overwrite:
            self.latitude = float(meta_dict.get('latitude'))

        if self.longitude is None or overwrite:
            self.longitude = float(meta_dict.get('longitude'))

        if self.timezone is None or overwrite:
            self.timezone = meta_dict.get('timezone')

        if self.name is None or overwrite:
            self.name = meta_dict.get('name')

        # Read weather data
        if self.data is None or overwrite:
            df = pd.read_csv(filename, skiprows=skiprows)
            self.data = df.set_index(
                pd.to_datetime(df['Unnamed: 0'])).tz_localize(
                'UTC').tz_convert(self.timezone).drop('Unnamed: 0', 1)

        # Define height dict
        self.data_height = {}
        for key in self.data.keys():
            self.data_height[key] = float(
                meta_dict.get('data_height' + key, 0))
        return self
