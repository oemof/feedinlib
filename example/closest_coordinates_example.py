import feedinlib.tools as tools
import pandas as pd
import os

from feedinlib import region

# loading weather data
filename = os.path.abspath('/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
weather_df = pd.read_csv(filename,
                         header=[0, 1], index_col=[0, 1, 2],
                         parse_dates=True)
# change type of height from str to int by resetting columns
weather_df.columns = [weather_df.axes[1].levels[0][
                          weather_df.axes[1].labels[0]],
                      weather_df.axes[1].levels[1][
                          weather_df.axes[1].labels[1]].astype(int)]

closest_coordinates = tools.get_closest_coordinates(
    weather_coordinates=weather_df, pp_location=[11.2, 52.3])
print(closest_coordinates)

# Example OPSD register
# todo: die datei wieder löschen
# todo: function wird in region.py aufgerufen
# todo: uninstall tables
with pd.HDFStore('opsd_temp.h5') as hdf_store:
    register = hdf_store.get('pp_data')
register = register.loc[register['energy_source_level_2'] == 'Wind'][0:10]

# adapted_register = tools.add_weather_locations_to_register(
#     register, weather_coordinates=weather_df)


# use region feedin
example_region = region.Region(geom='no_geom', weather=weather_df)
feedin = example_region.wind_feedin(register)