#!/usr/bin/env python
# coding: utf-8

"""
Process netCDF files (.nc) downloaded from the era5 downloaded from the
`Climate Data Store (CDS) <https://cds.climate.copernicus.eu>`_
"""
import os

import geopandas as gpd
import requests
import xarray as xr
from matplotlib import pyplot as plt
from shapely.geometry import Point

from feedinlib import Photovoltaic
from feedinlib.era5 import weather_df_from_era5


def era5_with_pvlib_examples(plot=True):
    data_path = os.path.join(os.path.dirname(__file__), "example_data")
    os.makedirs(data_path, exist_ok=True)

    # Download example files if they do not exist.
    files = {
        "zj6bg": "era5_feedinlib_54-16_9-08_2019-01-01_2019-12-31.nc",
        "96qyt": "germany_simple.geojson",
    }

    files = {k: os.path.join(data_path, v) for k, v in files.items()}

    for key, file in files.items():
        if not os.path.isfile(file):
            req = requests.get("https://osf.io/{0}/download".format(key))
            with open(file, "wb") as fout:
                fout.write(req.content)

    f, ax = plt.subplots(1, 2, figsize=(14, 5.6))

    # Read downloaded era5 file
    era5_netcdf_filename = files["zj6bg"]

    ds = xr.open_dataset(era5_netcdf_filename)

    # Extract the resulting coordinates from netCDF. These coordinates are the
    # nearest coordinates from era5 data points.
    points = []
    for x in ds.longitude:
        for y in ds.latitude:
            points.append(Point(x, y))
    points_df = gpd.GeoDataFrame({"geometry": points})

    # Read provided geojson file
    # It is also possible to open a Shapefile (.shp) with geopandas. It is also
    # no problem to convert a .shp-file to a .geojson file using geopandas or a
    # GUI such as qgis.
    region_shape = gpd.read_file(os.path.join(data_path, files["96qyt"]))

    # plot weather data points on map
    base = region_shape.plot(color="white", edgecolor="black", ax=ax[0])
    points_df.plot(ax=base, marker="o", color="red", markersize=5)

    # convert netcdf data to pandas.DataFrame
    pvlib_df = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename,
        lib="pvlib",
        area=list(points[0].coords[0]),
    )

    print(pvlib_df.head())

    system_data = {
        'module_name': 'Advent_Solar_Ventura_210___2008_',
        'inverter_name': 'ABB__MICRO_0_25_I_OUTD_US_208__208V_',
        'azimuth': 180,
        'tilt': 30,
        'albedo': 0.2}
    pv_system = Photovoltaic(**system_data)
    feedin = pv_system.feedin(
        weather=pvlib_df,
        location=(52.4, 13.2))
    ax[1].set_ylabel("power output")
    plt.tight_layout()
    feedin.fillna(0).plot(ax=ax[1])
    if plot is True:
        plt.show()


if __name__ == "__main__":
    era5_with_pvlib_examples()
