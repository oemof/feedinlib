# -*- coding: utf-8
"""
Example showing how to use the pvlib's and windpowerlib's ModelChain to
generate feed-in timeseries for a PV system and a wind turbine.
"""

import pandas as pd
import logging
try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None

import feedinlib.weather as weather

import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain as PVModelChain

from windpowerlib.modelchain import ModelChain as WindModelChain
from windpowerlib.wind_turbine import WindTurbine

logging.getLogger().setLevel(logging.INFO)

# loading feedinlib's weather data
my_weather = weather.FeedinWeather()
my_weather.read_feedinlib_csv('weather_wittenberg.csv')

# #####################################
# ********** windpowerlib *************
# #####################################

# preparing the weather data to suit the windpowerlib's needs

# The windpowerlib's ModelChain requires a weather DataFrame with time series
# for wind speed `wind_speed` in m/s, temperature `temperature` in K, roughness
# length `roughness_length` in m, and pressure `pressure` in Pa.
# The columns of the DataFrame need to be a MultiIndex where the first level
# contains the variable name as string (e.g. 'wind_speed') and the second level
# contains the height as integer in m at which it applies (e.g. 10, if it was
# measured at a height of 10 m).
data_height = {
    'pressure': 0,
    'temperature': 2,
    'wind_speed': 10,
    'roughness_length': 0}
weather_wind = pd.DataFrame(
    my_weather.data[['v_wind', 'temp_air', 'z0', 'pressure']])
weather_wind.columns = [['wind_speed', 'temperature',
                         'roughness_length', 'pressure'],
                        [data_height['wind_speed'],
                         data_height['temperature'],
                         data_height['roughness_length'],
                         data_height['pressure']]]

# initialize wind turbine

# The example here shows how to initialize a wind turbine object where the
# power curve is provided by the windpowerlib. See documentation of the
# windpowerlib if you want to know how to provide your own power (coefficient)
# curve.
enerconE126 = {
    'turbine_name': 'ENERCON E 126 7500',  # turbine name as in register
    'hub_height': 135,  # in m
    'rotor_diameter': 127  # in m
    }
e126 = WindTurbine(**enerconE126)

# calculate power output

# The windpowerlib's ModelChain class with its default settings is used here to
# calculate the power output. See the documentation of the windpowerlib if you
# want to learn more about the ModelChain.
mc_e126 = WindModelChain(e126).run_model(weather_wind)

# write power output timeseries to WindTurbine object
e126.power_output = mc_e126.power_output
if plt:
    e126.power_output.plot(legend=True, label='Enercon E126')
    plt.show()
else:
    print(e126.power_output)
    logging.warning("No plots shown. Install matplotlib to see the plots.")

# #####################################
# ********** pvlib ********************
# #####################################

# preparing the weather data to suit pvlib's needs

# The pvlib's ModelChain requires a weather DataFrame with time series
# for wind speed `wind_speed` in m/s, temperature `temp_air` in C, direct
# normal irradiation 'dni' in W/m², global horizontal irradiation 'ghi' in
# W/m², diffuse horizontal irradiation 'dhi' in W/m².
weather_pv = pd.DataFrame(
    my_weather.data[['v_wind', 'temp_air', 'dhi', 'dirhi']])
weather_pv.columns = ['wind_speed', 'temp_air', 'dhi', 'dirhi']
my_weather.data.rename(columns={'v_wind': 'wind_speed'}, inplace=True)
# temperature in degree Celsius instead of Kelvin
weather_pv['temp_air'] = weather_pv.temp_air - 273.15
# calculate ghi
weather_pv['ghi'] = weather_pv.dirhi + weather_pv.dhi

# initialize PV system

# get module and inverter parameter from sandia database
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')
invertername = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'
module_name = 'Yingli_YL210__2008__E__'
yingli210 = {
    'module_parameters': sandia_modules[module_name],
    'inverter_parameters': sapm_inverters[invertername],
    'surface_azimuth': 180,
    'surface_tilt': 60,
    'albedo': 0.2,
    }

# specify location
wittenberg = {
    'altitude': 34,
    'name': 'Wittenberg',
    'latitude': my_weather.latitude,
    'longitude': my_weather.longitude,
    }

# calculate power output

# The pvlib's ModelChain class with its default settings is used here to
# calculate the power output. See the documentation of the pvlib if you
# want to learn more about the ModelChain.
mc = PVModelChain(PVSystem(**yingli210),
                  Location(**wittenberg))
# use the ModelChain's complete_irradiance function to calculate missing dni
mc.complete_irradiance(times=weather_pv.index, weather=weather_pv)
mc.run_model() # times=weather_pv.index, weather=weather_pv)

if plt:
    mc.dc.p_mp.fillna(0).plot()
    plt.show()
else:
    print(mc.dc.p_mp)
    logging.warning("No plots shown. Install matplotlib to see the plots.")

logging.info('Done!')
