import feedinlib.tools as tools
import pandas as pd
import os

from feedinlib import region

# loading weather data
filename = os.path.abspath('/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
if not os.path.isfile(filename):
    raise FileNotFoundError("Please adjust the path.")
weather_df = pd.read_csv(filename,
                         header=[0, 1], index_col=[0, 1, 2],
                         parse_dates=True)
# change type of height from str to int by resetting columns
weather_df.columns = [weather_df.axes[1].levels[0][
                          weather_df.axes[1].labels[0]],
                      weather_df.axes[1].levels[1][
                          weather_df.axes[1].labels[1]].astype(int)]

# list
closest_coordinates = tools.get_closest_coordinates(
    weather_coordinates=weather_df, pp_location=[11.2, 52.3])
print(closest_coordinates)

# dataframe
df = pd.DataFrame([[51.2, 52.2, 51.0], [11.2, 12.2, 11.0]]).transpose().rename(columns={0: 'lat', 1: 'lon'})

coordinates = tools.get_closest_coordinates(
    weather_coordinates=weather_df, pp_location=df)

print(coordinates)
