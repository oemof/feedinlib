#!/usr/bin/python3
# -*- coding: utf-8

import pandas as pd
import logging

try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

import feedinlib.powerplants as plants
import feedinlib.models as models
import feedinlib.weather as weather

# Feel free to remove or change these lines
import warnings
warnings.simplefilter(action="ignore", category=RuntimeWarning)
logging.getLogger().setLevel(logging.INFO)


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
    'albedo': 0.2}

# Specification of the pv module
yingli210 = {
    'module_name': 'Yingli_YL210__2008__E__',
    'azimuth': 180,
    'tilt': 30,
    'albedo': 0.2}

# Specifications of the wind turbines
enerconE126 = {
    'h_hub': 135,
    'd_rotor': 127,
    'wind_conv_type': 'ENERCON E 126 7500'}

vestasV90 = {
    'h_hub': 105,
    'd_rotor': 90,
    'wind_conv_type': 'VESTAS V 90 3000'}


def ready_example_data(filename, datetime_column='Unnamed: 0'):
    df = pd.read_csv(filename)
    return df.set_index(pd.to_datetime(df[datetime_column])).tz_localize(
        'UTC').tz_convert('Europe/Berlin').drop(datetime_column, 1)


filename1 = 'weather.csv'
filename2 = 'weather_wittenberg.csv'

# Two Variants to create your weather object
# 1. Variant: Passing all data to the weather class
weather_df = ready_example_data(filename1)
my_weather_a = weather.FeedinWeather(
    data=weather_df,
    timezone='Europe/Berlin',
    latitude=52,
    longitude=13,
    data_height=coastDat2)

# 2. Variant: Loading a csv-file that has the feedinlib-csv-header (see docs)
my_weather_b = weather.FeedinWeather()
my_weather_b.read_feedinlib_csv(filename=filename2)

# Loading the weather data
my_weather = my_weather_b

# Initialise different power plants
# So far there is only one model available. So you do not have to pass a model
# (s. E126). If model is passed the default model is used.
# We hope that there will be different models in future versions. You can also
# write your own model an pass it to the powerplant.
E126_power_plant = plants.WindPowerPlant(**enerconE126)
V90_power_plant = plants.WindPowerPlant(model=models.SimpleWindTurbine,
                                        **vestasV90)

# Create a feedin series for a specific powerplant under specific weather
# conditions. One can define the number of turbines or the over all capacity.
# If no multiplier is set, the time series will be for one turbine.
E126_feedin = E126_power_plant.feedin(weather=my_weather, number=2)
V90_feedin = V90_power_plant.feedin(weather=my_weather,
                                    installed_capacity=15 * 10 ** 6)

E126_feedin.name = 'E126'
V90_feedin.name = 'V90'

if plt:
    E126_feedin.plot(legend=True)
    V90_feedin.plot(legend=True)
    plt.show()
else:
    print(V90_feedin)

# Initialise different power plants
# If you do not pass a model the default model is used. So far there is only
# one model available. This might change in future versions.
yingli_module = plants.Photovoltaic(**yingli210)
advent_module = plants.Photovoltaic(model=models.PvlibBased, **advent210)

pv_feedin1 = yingli_module.feedin(weather=my_weather, number=30000)
pv_feedin2 = yingli_module.feedin(weather=my_weather, area=15000)
pv_feedin3 = yingli_module.feedin(weather=my_weather, peak_power=15000)
pv_feedin4 = yingli_module.feedin(weather=my_weather)
pv_feedin5 = advent_module.feedin(weather=my_weather)

pv_feedin4.name = 'Yingli'
pv_feedin5.name = 'Advent'

# Output
if plt:
    pv_feedin4.plot(legend=True)
    pv_feedin5.plot(legend=True)
    plt.show()
else:
    print(pv_feedin5)

# Use directly methods of the model
# Write out all possible wind turbines.
w_model = models.SimpleWindTurbine()
w_model.get_wind_pp_types()

# Write out all possible pv-converters
print(models.PvlibBased().fetch_module_data(
    module_name='all', lib='sandia-modules').keys())

# Plot the cp curve of a wind turbine.
cp_values = models.SimpleWindTurbine().fetch_cp_values(
    wind_conv_type='ENERCON E 126 7500')
if plt:
    plt.plot(cp_values.loc[0, :][2:55].index,
             cp_values.loc[0, :][2:55].values, '*')
    plt.show()
else:
    # The value for 8 m/s
    index = cp_values.loc[0, :][2:55].index == '8'
    print(cp_values.loc[0, :][2:55].values[index][0])

logging.info('Done!')
