#!/usr/bin/python3
# -*- coding: utf-8

import pandas as pd
import logging
import os
try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve

try:
    from matplotlib import pyplot as plt
    plot_fkt = True
except:
    plot_fkt = False

from feedinlib import powerplants as plants
from feedinlib import models

# Feel free to remove or change these lines
import warnings
warnings.simplefilter(action="ignore", category=RuntimeWarning)
logging.getLogger().setLevel(logging.INFO)

# Specification of the wind model
required_parameter_wind = {
    'h_hub': 'height of the hub in meters',
    'd_rotor': 'diameter of the rotor in meters',
    'wind_conv_type': 'wind converter according to the list in the csv file.',
    'data_height': 'dictionary containing the heights of the data model'}

# Specification of the pv model
required_parameter_pv = {
    'azimuth': 'Azimuth angle of the pv module',
    'tilt': 'Tilt angle of the pv module',
    'module_name': 'According to the sandia module library.',
    'albedo': 'Albedo value',
    'tz': 'Time zone',
    'longitude': 'Position of the weather data (longitude)',
    'latitude': 'Position of the weather data (latitude)'}

# Specification of the weather data set CoastDat2
coastDat2 = {
    'dhi': 0,
    'dirhi': 0,
    'pressure': 0,
    'temp_air': 2,
    'v_wind': 10,
    'Z0': 0}

# Specification of the pv module
advent210 = {
    'module_name': 'Advent_Solar_Ventura_210___2008_',
    'azimuth': 180,
    'tilt': 30,
    'albedo': 0.2,
    'tz': 'Europe/Berlin',
    'latitude': 52,
    'longitude': 12}

# Specification of the pv module
yingli210 = {
    'module_name': 'Yingli_YL210__2008__E__',
    'azimuth': 180,
    'tilt': 30,
    'albedo': 0.2,
    'tz': 'Europe/Berlin',
    'latitude': 52,
    'longitude': 12}

# Specifications of the wind turbines
enerconE126 = {
    'h_hub': 135,
    'd_rotor': 127,
    'wind_conv_type': 'ENERCON E 126 7500',
    'data_height': coastDat2}

vestasV90 = {
    'h_hub': 105,
    'd_rotor': 90,
    'wind_conv_type': 'VESTAS V 90 3000',
    'data_height': coastDat2}


def ready_example_data():
    basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
    filename = os.path.join(basic_path, 'weather.csv')
    url = 'http://vernetzen.uni-flensburg.de/~git/weather.csv'
    if not os.path.exists(basic_path):
        os.makedirs(basic_path)
    if not os.path.isfile(filename):
        logging.info('Copying weather data from {0} to {1}'.format(
            url, filename))
        urlretrieve(url, filename)
    df = pd.read_csv(filename)
    return df.set_index(pd.to_datetime(df['Unnamed: 0'])).tz_localize(
        'UTC').tz_convert('Europe/Berlin').drop('Unnamed: 0', 1)

# Loading the weather data
my_weather_df = ready_example_data()

# TODO@gnn: remove required parameters
required = list(required_parameter_wind.keys())

# Initialise different power plants
# TODO@gnn: make required parameters optional
E126_power_plant = plants.WindPowerPlant(model=models.WindPowerPlant(required),
                                         **enerconE126)
V90_power_plant = plants.WindPowerPlant(model=models.WindPowerPlant(required),
                                        **vestasV90)

# Create a feedin series for a specific powerplant under specific weather
# conditions. One can define the number of turbines or the over all capacity.
# If no multiplier is set, the time series will be for one turbine.
E126_feedin = E126_power_plant.feedin(data=my_weather_df, number=2)
V90_feedin = V90_power_plant.feedin(
    data=my_weather_df, installed_capacity=15000)

E126_feedin.name = 'E126'
V90_feedin.name = 'V90'

if plot_fkt:
    E126_feedin.plot(legend=True)
    V90_feedin.plot(legend=True)
    plt.show()
else:
    print(V90_feedin)

# TODO@gnn: remove required parameters
required = list(required_parameter_pv.keys())

# Initialise different power plants
# TODO@gnn: make required parameters optional
yingli_module = plants.Photovoltaic(model=models.Photovoltaic(required),
                                    **yingli210)
advent_module = plants.Photovoltaic(model=models.Photovoltaic(required),
                                    **advent210)

pv_feedin1 = yingli_module.feedin(data=my_weather_df, number=30000)
pv_feedin2 = yingli_module.feedin(data=my_weather_df, area=15000)
pv_feedin3 = yingli_module.feedin(data=my_weather_df, peak_power=15000)
pv_feedin4 = yingli_module.feedin(data=my_weather_df)
pv_feedin5 = advent_module.feedin(data=my_weather_df)

pv_feedin4.name = 'Yingli'
pv_feedin5.name = 'Advent'

# Output
if plot_fkt:
    pv_feedin4.plot(legend=True)
    pv_feedin5.plot(legend=True)
    plt.show()
else:
    print(pv_feedin5)

# Use directly methods of the model
w_model = models.WindPowerPlant(required=[])
w_model.get_wind_pp_types()
cp_values = models.WindPowerPlant(required=[]).fetch_cp_values(
    wind_conv_type='ENERCON E 126 7500')
if plot_fkt:
    plt.plot(cp_values.loc[0, :][2:55].index,
             cp_values.loc[0, :][2:55].values, '*')
    plt.show()
else:
    print(cp_values.loc[0, :][2:55].values)

logging.info('Done!')
