# -*- coding: utf-8
"""
Using the pvlib with feedinlib's weather object.
Using the windpowerlib with feedinlib's weather object.
"""

from matplotlib import pyplot as plt
import pvlib
import logging
import os
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.tools import cosd
import feedinlib.weather as weather
from windpowerlib import basicmodel
from urllib.request import urlretrieve


def download_file(filename, url):
    if not os.path.isfile(filename):
        logging.info('Copying weather data from {0} to {1}'.format(
            url, filename))
        urlretrieve(url, filename)
        txt = "The example files are store to the '.oemof' folder of your home "
        txt += "directory."
        logging.info(txt)


def fetch_example_files():
    basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
    filename_csv1 = os.path.join(basic_path, 'weather.csv')
    url1 = 'http://vernetzen.uni-flensburg.de/~git/weather.csv'
    filename_csv2 = os.path.join(basic_path, 'weather_wittenberg.csv')
    url2 = 'http://vernetzen.uni-flensburg.de/~git/weather_wittenberg.csv'
    if not os.path.exists(basic_path):
        os.makedirs(basic_path)
    download_file(filename_csv1, url1)
    download_file(filename_csv2, url2)
    return filename_csv1, filename_csv2


logging.getLogger().setLevel(logging.INFO)

# loading feedinlib's weather data
filename1, filename2 = fetch_example_files()
my_weather = weather.FeedinWeather()
my_weather.read_feedinlib_csv(filename2)

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

e126.turbine_power_output(weather=my_weather.data, data_height=coastDat2).plot()
plt.show()

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
# divide into irradiance (i) and weather (w)
i = my_weather.data.loc[:, ['ghi', 'dhi']]
w = my_weather.data.loc[:, ['temp_air', 'wind_speed']]

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

# in my opinion this part should be part of pvlib's ModelChain (run_model)
# from pvlib.tools import cosd
# if irradiance.get('dni') is None:
#     irradiance['dni'] = (irradiance.ghi - irradiance.dhi) /
#                          cosd(self.solar_position.zenith)
if i.get('dni') is None:
    i['dni'] = (i.ghi - i.dhi) / cosd(
        Location(**wittenberg).get_solarposition(times).zenith)

# pvlib's ModelChain
mc = ModelChain(PVSystem(**yingli210),
                Location(**wittenberg),
                orientation_strategy='south_at_latitude_tilt')

mc.run_model(times, irradiance=i, weather=w)

# plot the results
mc.dc.p_mp.fillna(0).plot()

logging.info('Done!')
