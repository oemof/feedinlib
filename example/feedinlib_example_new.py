# -*- coding: utf-8
"""
Using the pvlib with feedinlib's weather object.
Using the windpowerlib with feedinlib's weather object.
"""

try:
    from matplotlib import pyplot as plt
except ImportError:
    plt = None
import pvlib
import logging
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.tools import cosd
import feedinlib.weather as weather
from windpowerlib import basicmodel


logging.getLogger().setLevel(logging.INFO)

# loading feedinlib's weather data
my_weather = weather.FeedinWeather()
my_weather.read_feedinlib_csv('weather_wittenberg.csv')

# #####################################
# ********** windpowerlib *************
# #####################################

# specifications of the weather data set
coastDat2 = {
    'dhi': 0,
    'dirhi': 0,
    'pressure': 0,
    'temp_air': 2,
    'v_wind': 10,
    'Z0': 0}

# own parameters of the wind converter
enerconE126 = {
    'h_hub': 135,
    'd_rotor': 127,
    'wind_conv_type': 'ENERCON E 126 7500'}

# windpowerlib's basic model
e126 = basicmodel.SimpleWindTurbine(**enerconE126)

if plt:
    e126.turbine_power_output(weather=my_weather.data,
        data_height=coastDat2).plot()
    plt.show()
else:
    logging.warning("No plots shown. Install matplotlib to see the plots.")

# #####################################
# ********** pvlib ********************
# #####################################

# preparing the weather data to suit pvlib's needs
# different name for the wind speed
my_weather.data.rename(columns={'v_wind': 'wind_speed'}, inplace=True)
# temperature in degree Celsius instead of Kelvin
my_weather.data['temp_air'] = my_weather.data.temp_air - 273.15
# calculate ghi
my_weather.data['ghi'] = my_weather.data.dirhi + my_weather.data.dhi
w = my_weather.data

# time index from weather data set
times = my_weather.data.index

# get module and inverter parameter from sandia database
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('sandiainverter')

# own module parameters
invertername = 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_'
yingli210 = {
    'module_parameters': sandia_modules['Yingli_YL210__2008__E__'],
    'inverter_parameters': sapm_inverters[invertername],
    'surface_azimuth': 180,
    'surface_tilt': 60,
    'albedo': 0.2,
    }

# own location parameter
wittenberg = {
    'altitude': 34,
    'name': 'Wittenberg',
    'latitude': my_weather.latitude,
    'longitude': my_weather.longitude,
    }

# the following has been implemented in the pvlib ModelChain in the
# complete_irradiance method (pvlib version > v0.4.5)
if w.get('dni') is None:
    w['dni'] = (w.ghi - w.dhi) / cosd(
        Location(**wittenberg).get_solarposition(times).zenith)

# pvlib's ModelChain
mc = ModelChain(PVSystem(**yingli210),
                Location(**wittenberg),
                orientation_strategy='south_at_latitude_tilt')

mc.run_model(times, weather=w)

if plt:
    mc.dc.p_mp.fillna(0).plot()
    plt.show()
else:
    logging.warning("No plots shown. Install matplotlib to see the plots.")

logging.info('Done!')
