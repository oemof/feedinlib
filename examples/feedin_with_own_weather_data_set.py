import os

import matplotlib.pyplot as plt
import pandas as pd
import requests

from feedinlib import Photovoltaic
from feedinlib import WindPowerPlant


def run_example():
    data_path = os.path.join(os.path.dirname(__file__), "example_data")
    os.makedirs(data_path, exist_ok=True)

    # Download example files if they do not exist.
    files = {
        "etkfg": "weather.csv",
    }

    files = {k: os.path.join(data_path, v) for k, v in files.items()}

    for key, file in files.items():
        if not os.path.isfile(file):
            req = requests.get("https://osf.io/{0}/download".format(key))
            with open(file, "wb") as fout:
                fout.write(req.content)

    # ######## set up weather dataframes (temporary) #########

    # set up weather dataframe for windpowerlib
    filename = os.path.join(
        os.path.dirname(__file__), "example_data/weather.csv"
    )
    weather_df_wind = pd.read_csv(
        filename,
        index_col=0,
        date_parser=lambda idx: pd.to_datetime(idx, utc=True),
    )
    # change type of index to datetime and set time zone
    weather_df_wind.index = pd.to_datetime(weather_df_wind.index).tz_convert(
        "Europe/Berlin"
    )
    data_height = {
        "pressure": 0,
        "temperature": 2,
        "wind_speed": 10,
        "roughness_length": 0,
    }
    weather_df_wind = weather_df_wind[["v_wind", "temp_air", "z0", "pressure"]]
    weather_df_wind.columns = [
        ["wind_speed", "temperature", "roughness_length", "pressure"],
        [
            data_height["wind_speed"],
            data_height["temperature"],
            data_height["roughness_length"],
            data_height["pressure"],
        ],
    ]

    # set up weather dataframe for pvlib
    weather_df_pv = pd.read_csv(
        filename,
        index_col=0,
        date_parser=lambda idx: pd.to_datetime(idx, utc=True),
    )
    # change type of index to datetime and set time zone
    weather_df_pv.index = pd.to_datetime(weather_df_pv.index).tz_convert(
        "Europe/Berlin"
    )
    weather_df_pv["temp_air"] = weather_df_pv.temp_air - 273.15
    weather_df_pv["ghi"] = weather_df_pv.dirhi + weather_df_pv.dhi
    weather_df_pv.rename(columns={"v_wind": "wind_speed"}, inplace=True)

    # ######## Pvlib model #########

    # specify pv system
    system_data = {
        "module_name": "Advent_Solar_Ventura_210___2008_",
        "inverter_name": "ABB__MICRO_0_25_I_OUTD_US_208__208V_",
        "azimuth": 180,
        "tilt": 30,
        "albedo": 0.2,
    }

    # instantiate feedinlib Photovoltaic object
    pv_module = Photovoltaic(**system_data)

    # calculate feedin
    feedin = pv_module.feedin(
        weather=weather_df_pv[["wind_speed", "temp_air", "dhi", "ghi"]],
        location=(52, 13),
        scaling="peak_power",
        scaling_value=10,
    )

    # plot
    feedin.fillna(0).plot(title="PV feedin")
    plt.xlabel("Time")
    plt.ylabel("Power in W")
    plt.show()

    # ######## WindpowerlibTurbine model #########

    # specify wind turbine
    enercon_e82 = {
        "turbine_type": "E-82/3000",  # turbine name as in register
        "hub_height": 135,  # in m
    }

    # instantiate feedinlib WindPowerPlant object (single turbine)
    e82 = WindPowerPlant(**enercon_e82)

    # calculate feedin
    feedin = e82.feedin(weather=weather_df_wind, location=(52, 13))
    feedin_scaled = e82.feedin(
        weather=weather_df_wind,
        location=(52, 13),
        scaling="nominal_power",
        scaling_value=5e6,
    )

    feedin_scaled.fillna(0).plot(
        legend=True, label="scaled to 5 MW", title="Wind turbine feedin"
    )
    feedin.fillna(0).plot(legend=True, label="single turbine")
    plt.xlabel("Time")
    plt.ylabel("Power in W")
    plt.show()


if __name__ == "__main__":
    run_example()
