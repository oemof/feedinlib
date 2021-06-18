"""
Read the single_location examples first.

"""

import json
import os

import geopandas as gpd
import requests
import xarray as xr
from matplotlib import pyplot as plt
from shapely.geometry import GeometryCollection
from shapely.geometry import Point
from shapely.geometry import Polygon
from shapely.geometry import shape

from feedinlib import Photovoltaic
from feedinlib import WindPowerPlant
from feedinlib.era5 import weather_df_from_era5


def processing_multi_locations():
    data_path = os.path.join(os.path.dirname(__file__), "example_data")
    os.makedirs(data_path, exist_ok=True)

    # Download example files if they do not exist.
    files = {
        "zncmb": "era5_feedinlib_berlin_2017.nc",
        "txmze": "berlin_shape.geojson",
        "96qyt": "germany_simple.geojson",
    }

    files = {k: os.path.join(data_path, v) for k, v in files.items()}

    for key, file in files.items():
        if not os.path.isfile(file):
            req = requests.get("https://osf.io/{0}/download".format(key))
            with open(file, "wb") as fout:
                fout.write(req.content)

    # The example netCDF-file is fetched from the era5-server with the
    # following bounding box: latitude = [52.3, 52.7]  longitude = [13.1, 13.7]

    # Read the netCDF-file into an xarray
    era5_netcdf_filename = files["zncmb"]
    # era5_netcdf_filename = "example_data/ERA5_example_data.nc"
    ds = xr.open_dataset(era5_netcdf_filename)

    # Extract all points from the netCDF-file:
    points = []
    for x in ds.longitude:
        for y in ds.latitude:
            points.append(Point(x, y))
    points_df = gpd.GeoDataFrame({"geometry": points})

    # Plot all points within the bounding box with the shape of Berlin
    region_shape = gpd.read_file(
        os.path.join(data_path, "berlin_shape.geojson")
    )
    base = region_shape.plot(color="white", edgecolor="black")
    points_df.plot(ax=base, marker="o", color="red", markersize=5)
    plt.show()

    # With the `area` parameter you can specify a spatial subset of the weather
    # data in your netCDF-file.
    # In case `area` is not a single location, the index of the resulting
    # dataframe will be a multiindex with levels (time, latitude, longitude).
    # Be aware that in order to use it for pvlib or windpowerlib calculations
    # you need to select just one location.

    # Create a pandas DataFrame for all locations.
    pvlib_all = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename, lib="pvlib"
    )

    print("All points:\n", pvlib_all.groupby(level=[1, 2]).mean().index)

    # Create a pandas DataFrame for a bounding box.
    area = [(13.2, 13.4), (52.4, 52.8)]
    pvlib_bb = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename, lib="pvlib", area=area
    )
    print(
        "Bounding box points:\n", pvlib_bb.groupby(level=[1, 2]).mean().index
    )

    # Create a pandas DataFrame for a polygon.
    lat_point_list = [52.1, 52.1, 52.65]
    lon_point_list = [13.0, 13.4, 13.4]
    area = Polygon(zip(lon_point_list, lat_point_list))
    pvlib_polygon = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename, lib="pvlib", area=area
    )
    print(
        "Polygon points:\n", pvlib_polygon.groupby(level=[1, 2]).mean().index
    )

    # Create a pandas DataFrame for a multipolygon.
    with open(os.path.join(data_path, "germany_simple.geojson")) as f:
        features = json.load(f)["features"]
    polygon = GeometryCollection(
        [shape(feature["geometry"]).buffer(0) for feature in features]
    )
    area = polygon
    pvlib_polygon_real = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename, lib="pvlib", area=area
    )
    print(
        "Multipolygon points:\n",
        pvlib_polygon_real.groupby(level=[1, 2]).mean().index,
    )

    # Create a pandas DataFrame for single location and a time subset (pv)
    start = "2017-07-01"
    end = "2017-07-31"
    single_location = [13.2, 52.4]
    pvlib_single = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename,
        lib="pvlib",
        area=single_location,
        start=start,
        end=end,
    )

    system_data = {
        "module_name": "Advent_Solar_Ventura_210___2008_",
        "inverter_name": "ABB__MICRO_0_25_I_OUTD_US_208__208V_",
        "azimuth": 180,
        "tilt": 30,
        "albedo": 0.2,
    }
    pv_system = Photovoltaic(**system_data)
    feedin = pv_system.feedin(weather=pvlib_single, location=(52.5, 13.1))
    feedin.plot()

    plt.show()

    # Create a pandas DataFrame for single location and a time subset (pv)
    start = "2017-07-01"
    end = "2017-07-31"
    single_location = [13.2, 52.4]
    windpowerlib_single = weather_df_from_era5(
        era5_netcdf_filename=era5_netcdf_filename,
        lib="windpowerlib",
        area=single_location,
        start=start,
        end=end,
    )

    turbine_data = {"turbine_type": "E-101/3050", "hub_height": 135}
    wind_turbine = WindPowerPlant(**turbine_data)
    feedin = wind_turbine.feedin(weather=windpowerlib_single)
    feedin.plot()

    plt.show()


if __name__ == "__main__":
    processing_multi_locations()
