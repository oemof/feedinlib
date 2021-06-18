#!/usr/bin/env python
# coding: utf-8

"""
Process netCDF files (.nc) downloaded from the era5 downloaded from the
`Climate Data Store (CDS) <https://cds.climate.copernicus.eu>`_
"""
import os

import pandas as pd
import requests
from matplotlib import pyplot as plt

from feedinlib import WindPowerPlant
from feedinlib.era5 import weather_df_from_era5
from feedinlib.models import WindpowerlibTurbineCluster


def cluster_and_windfarm_examples():
    data_path = os.path.join(os.path.dirname(__file__), "example_data")
    os.makedirs(data_path, exist_ok=True)

    # Download example files if they do not exist.
    files = {
        "2enha": "era5_windpowerlib_54-43_7-68_2019-01-01_2019-12-31.nc",
        "zj6bg": "era5_feedinlib_54-16_9-08_2019-01-01_2019-12-31.nc",
        "96qyt": "germany_simple.geojson",
    }

    files = {k: os.path.join(data_path, v) for k, v in files.items()}

    for key, file in files.items():
        if not os.path.isfile(file):
            req = requests.get("https://osf.io/{0}/download".format(key))
            with open(file, "wb") as fout:
                fout.write(req.content)

    # convert netcdf data to pandas.DataFrame
    windpowerlib_df = weather_df_from_era5(
        era5_netcdf_filename=files["zj6bg"], lib="windpowerlib", area=[5, 3]
    )

    # ######## WindpowerlibTurbineCluster model #########

    # specify (and instantiate) wind turbines
    enercon_e82 = {
        "turbine_type": "E-82/3000",  # turbine name as in register
        "hub_height": 135,  # in m
    }

    vestas_v90 = {
        "turbine_type": "V90/2000",  # turbine name as in register
        "hub_height": 120,  # in m
    }

    # instantiate feedinlib WindPowerPlant object with
    # WindpowerlibTurbineCluster model

    # wind farms need a wind turbine fleet specifying the turbine types in
    # the farm and their number or total installed capacity
    # the wind turbines can either be provided in the form of a
    # pandas.DataFrame
    farm1 = {
        "wind_turbine_fleet": pd.DataFrame(
            {
                "wind_turbine": [enercon_e82, vestas_v90],
                "number_of_turbines": [6, None],
                "total_capacity": [None, 3 * 2e6],
            }
        )
    }
    windfarm1 = WindPowerPlant(**farm1, model=WindpowerlibTurbineCluster)

    farm2 = {
        "wind_turbine_fleet": pd.DataFrame(
            {
                "wind_turbine": [enercon_e82, vestas_v90],
                "number_of_turbines": [2, None],
                "total_capacity": [None, 6e6],
            }
        )
    }
    windfarm2 = WindPowerPlant(**farm2, model=WindpowerlibTurbineCluster)

    # wind turbine clusters need a list of wind farms (specified as
    # dictionaries) in that cluster
    cluster = {"wind_farms": [farm1, farm2]}
    windcluster = WindPowerPlant(**cluster, model=WindpowerlibTurbineCluster)

    # calculate feedin
    feedin1 = windfarm1.feedin(weather=windpowerlib_df, location=(52, 13))
    feedin2 = windfarm2.feedin(weather=windpowerlib_df, location=(52, 13))
    feedin3 = windcluster.feedin(weather=windpowerlib_df, location=(52, 13))

    feedin3.fillna(0).plot(legend=True, label="Wind cluster")
    feedin1.fillna(0).plot(legend=True, label="Windfarm 1")
    feedin2.fillna(0).plot(
        legend=True, label="Windfarm 2", title="Wind cluster feedin"
    )

    plt.xlabel("Time")
    plt.ylabel("Power in W")
    plt.show()


if __name__ == "__main__":
    cluster_and_windfarm_examples()
