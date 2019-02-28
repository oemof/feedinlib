#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 10:24:40 2019

@author: RL-INSTITUT\inia.steinbach

"""
import xarray as xr
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

from feedinlib import tools
from feedin_germany import opsd_power_plants as opsd
from feedin_germany import pv_modules as modules
from feedinlib import Photovoltaic, WindPowerPlant


output = pd.Series()
# -> weise jeder Anlage eine Wetterzelle zu (pd.cut) bzw. ersetze lat,lon mit Wetter-Koordinaten 
filename = os.path.abspath("/home/local/RL-INSTITUT/inia.steinbach/mount_ordner/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_test_2016.csv")
if not os.path.isfile(filename):
    raise FileNotFoundError("Please adjust the path.")
weather_df = pd.read_csv(filename,skiprows=range(1, 50), nrows=(5000), index_col=0, date_parser=lambda idx: pd.to_datetime(idx, utc=True))
weather_df.index = pd.to_datetime(weather_df.index).tz_convert(
    'Europe/Berlin')
# temperature in degree Celsius instead of Kelvin
#weather_df['temp_air'] = weather_df.temp_air - 273.15
# calculate ghi
weather_df['ghi'] = weather_df.dirhi + weather_df.dhi
#weather_df.rename(columns={'v_wind': 'wind_speed'}, inplace=True)

df=weather_df.dropna()

register_pv = opsd.filter_pp_by_source_and_year(year=2013, energy_source='Solar')

register_pv_locations = tools.add_weather_locations_to_register(
    register=register_pv, weather_coordinates=weather_df)

#calculate installed capacity per weathercell
installed_capacity= register_pv_locations.groupby(
    ['weather_lat', 'weather_lon'])['capacity'].agg('sum').reset_index()
# import technical parameters
technical_parameters = modules.create_pvmodule_dict()
#print(technical_parameters['LG290G3_2'])
    
    
distribution_dict = modules.create_distribution_dict()

for index, row in installed_capacity.iterrows():
    for key in technical_parameters.keys():
        module = technical_parameters[key]
        pv_system = Photovoltaic(**module)
        lat=row['weather_lat']
        lon=row['weather_lon']
        weather= df.loc[(df['lat'] == lat) & (df['lon'] == lon)]
        #calculate the feedin and set the scaling to 'area' or 'peak_power'
        feedin = pv_system.feedin(
            weather=weather[['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
            location=(lat, lon))
        feedin_scaled = pv_system.feedin(
            weather=weather[['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
            location=(lat, lon), scaling='peak_power', scaling_value=10)
        # get the distribution for the pv_module
        dist = distribution_dict[key]
        local_installed_capacity = row['capacity']
        # scale the output with the module_distribution and the local installed capacity
        module_feedin = feedin_scaled.multiply(dist*local_installed_capacity)
#        # add the module output to the output series
        output=output.add(other=module_feedin, fill_value=0)


output.fillna(0).plot()
#feedin.fillna(0).plot()
plt.show()
