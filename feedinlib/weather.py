# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 16:01:02 2015

@author: uwe
"""

import pandas as pd


class FeedinWeather:
    def __init__(self, **kwargs):
        r"""
        """
        self.data = kwargs.get('data', None)
        self.timezone = kwargs.get('timezone', None)
        self.longitude = kwargs.get('longitude', None)
        self.latitude = kwargs.get('latitude', None)
        self.name = kwargs.get('name', None)
        self.data_height = kwargs.get('data_height', None)

    def read_feedinlib_csv(self, filename=None, overwrite=True):
        r"""
        Raises: FileNotFoundError
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
