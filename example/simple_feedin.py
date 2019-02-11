from feedinlib import Photovoltaic, WindPowerPlant
import pandas as pd

# PV
yingli210 = {
    'module_name': 'Yingli_YL210__2008__E__',
    'inverter_name': 'ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_',
    'azimuth': 180,
    'tilt': 30,
    'albedo': 0.2}

yingli_module = Photovoltaic(**yingli210)
print(yingli_module)

weather_df = pd.read_csv(
    'weather.csv', index_col=0,
    date_parser=lambda idx: pd.to_datetime(idx, utc=True))
# change type of index to datetime and set time zone
weather_df.index = pd.to_datetime(weather_df.index).tz_convert(
    'Europe/Berlin')
# temperature in degree Celsius instead of Kelvin
weather_df['temp_air'] = weather_df.temp_air - 273.15
# calculate ghi
weather_df['ghi'] = weather_df.dirhi + weather_df.dhi
weather_df.rename(columns={'v_wind': 'wind_speed'}, inplace=True)

weather_pvlib = weather_df.copy()

feedin = yingli_module.feedin(weather=weather_df[['wind_speed', 'temp_air', 'dhi', 'dirhi', 'ghi']],
                     location=(52, 13))

feedin.fillna(0).plot()

# Wind
enerconE126 = {
    'name': 'E-82/3000',  # turbine name as in register
    'hub_height': 135,  # in m
    'fetch_curve': 'power_curve'
    }
e126 = WindPowerPlant(**enerconE126)

weather_df = pd.read_csv(
    'weather.csv', index_col=0,
    date_parser=lambda idx: pd.to_datetime(idx, utc=True))
# change type of index to datetime and set time zone
weather_df.index = pd.to_datetime(weather_df.index).tz_convert(
    'Europe/Berlin')
data_height = {
    'pressure': 0,
    'temperature': 2,
    'wind_speed': 10,
    'roughness_length': 0}
weather_df = weather_df[['v_wind', 'temp_air', 'z0', 'pressure']]
weather_df.columns = [['wind_speed', 'temperature',
                         'roughness_length', 'pressure'],
                        [data_height['wind_speed'],
                         data_height['temperature'],
                         data_height['roughness_length'],
                         data_height['pressure']]]

feedin = e126.feedin(weather=weather_df,
                     location=(52, 13))

feedin.fillna(0).plot()

