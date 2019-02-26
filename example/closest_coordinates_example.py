import feedinlib.tools as tools
import pandas as pd
import os

# loading weather data
filename = os.path.abspath('/home/sabine/rl-institut/04_Projekte/163_Open_FRED/03-Projektinhalte/AP2 Wetterdaten/open_FRED_TestWetterdaten_csv/fred_data_2016_sh.csv')
weather_df = tools.example_weather_wind(filename)

# list
closest_coordinates = tools.get_closest_coordinates(
    weather_coordinates=weather_df, pp_locations=[11.2, 52.3])
print(closest_coordinates)

# dataframe
df = pd.DataFrame([[51.2, 52.2, 51.0], [11.2, 12.2, 11.0]]).transpose().rename(
    columns={0: 'lat', 1: 'lon'})

coordinates = tools.get_closest_coordinates(
    weather_coordinates=weather_df, pp_locations=df)

print(coordinates)
