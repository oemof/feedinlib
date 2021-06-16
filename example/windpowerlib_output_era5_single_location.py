#!/usr/bin/env python
# coding: utf-8

"""
Process netCDF files (.nc) downloaded from the era5 downloaded from the
`Climate Data Store (CDS) <https://cds.climate.copernicus.eu>`_
"""

import geopandas as gpd
import xarray as xr
from matplotlib import pyplot as plt
from shapely.geometry import Point

from feedinlib import WindPowerPlant
from feedinlib.era5 import weather_df_from_era5

f, ax = plt.subplots(1, 2, figsize=(14, 5.6))

# Read downloaded era5 file
era5_netcdf_filename = "era5_feedinlib_54-16_9-08_2019-01-01_2019-12-31.nc"
# era5_netcdf_filename = "era5_feedinlib_54-43_7-68_2019-01-01_2019-12-31.nc"
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
region_shape = gpd.read_file("germany_simple.geojson")

# plot weather data points on map
base = region_shape.plot(color="white", edgecolor="black", ax=ax[0])
points_df.plot(ax=base, marker="o", color="red", markersize=5)

# for whole region
windpowerlib_df = weather_df_from_era5(
    era5_netcdf_filename=era5_netcdf_filename,
    lib="windpowerlib",
    area=list(points[0].coords[0]),
)

print(windpowerlib_df.head())

turbine_data = {"turbine_type": "E-101/3050", "hub_height": 135}
wind_turbine = WindPowerPlant(**turbine_data)
feedin = wind_turbine.feedin(weather=windpowerlib_df)
feedin.plot(ax=ax[1])
ax[1].set_ylabel("power output")
plt.tight_layout()
plt.show()
