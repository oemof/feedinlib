import json
import os

import pandas as pd
import pytest
import requests
from shapely.geometry import GeometryCollection
from shapely.geometry import Polygon
from shapely.geometry import shape
from shapely.geometry import Point

from feedinlib.era5 import weather_df_from_era5
from feedinlib.era5 import extract_coordinates_from_era5


class TestEra5MultiLocation:
    @classmethod
    def setup_class(cls):
        data_path = os.path.join(os.path.dirname(__file__), "test_data")
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

        cls.era5_netcdf_file = files["zncmb"]
        cls.geo_germany = files["96qyt"]
        cls.geo_berlin = files["txmze"]

    def test_big_bounding_box(self):
        area = [(13.2, 13.4), (52.4, 52.8)]
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file, lib="pvlib", area=area
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 2
        coords_round = [round(p, 2) for c in coords for p in c]
        assert coords_round == [52.55, 13.35, 52.8, 13.35]

    def test_empty_bounding_box(self):
        area = [(17.2, 17.4), (53.4, 53.8)]
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file, lib="pvlib", area=area
        )
        assert len(weather) == 0
        assert isinstance(weather, pd.DataFrame)

    def test_small_bounding_box(self):
        area = [(13.2, 13.4), (52.4, 52.6)]
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file, lib="pvlib", area=area
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 1
        coords_round = [round(p, 2) for c in coords for p in c]
        assert coords_round == [52.55, 13.35]

    def test_big_polygon(self):
        lat_point_list = [52.1, 52.1, 52.65]
        lon_point_list = [13.0, 13.4, 13.4]
        area = Polygon(zip(lon_point_list, lat_point_list))
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 2
        coords_round = [round(p, 2) for c in coords for p in c]
        assert coords_round == [52.3, 13.35, 52.55, 13.35]

    def test_empty_polygon(self):
        lat_point_list = [53.1, 53.1, 53.65]
        lon_point_list = [15.0, 15.4, 15.4]
        area = Polygon(zip(lon_point_list, lat_point_list))
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        assert len(weather) == 0
        assert isinstance(weather, pd.DataFrame)

    def test_small_polygon(self):
        lat_point_list = [52.35, 52.35, 52.65]
        lon_point_list = [13.0, 13.4, 13.4]
        area = Polygon(zip(lon_point_list, lat_point_list))
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 1
        coords_round = [round(p, 2) for c in coords for p in c]
        assert coords_round == [52.55, 13.35]

    def test_no_area(self):
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file, lib="windpowerlib"
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 9
        assert len(weather.index) == 78840

    def test_time_filter(self):
        start = "2017-07-01"
        end = "2017-07-02"
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            start=start,
            end=end,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 9
        assert len(weather.index) / len(coords) == 25

    def test_with_germany_polygon(self):
        with open(self.geo_germany) as f:
            features = json.load(f)["features"]
        area = GeometryCollection(
            [shape(feature["geometry"]).buffer(0) for feature in features]
        )
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 9

    def test_with_berlin_polygon(self):
        with open(self.geo_berlin) as f:
            features = json.load(f)["features"]
        area = GeometryCollection(
            [shape(feature["geometry"]).buffer(0) for feature in features]
        )
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 1
        coords_round = [round(p, 2) for c in coords for p in c]
        assert coords_round == [52.55, 13.35]

    def test_with_matching_single_point(self):
        points = extract_coordinates_from_era5(self.era5_netcdf_file)
        area = points[0]
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 1

    def test_with_nearest_single_point(self):
        area = Point(12, 52)
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
            drop_coord_levels=True
        )
        assert not isinstance(weather.index, pd.MultiIndex)
        assert weather.index.name == (52.3, 13.1)

    def test_with_nearest_single_point_list(self):
        area = [12, 52]
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
            drop_coord_levels=True
        )
        assert not isinstance(weather.index, pd.MultiIndex)
        assert weather.index.name == (52.3, 13.1)

    def test_with_single_coordinate(self):
        # points = extract_coordinates_from_era5(self.era5_netcdf_file)
        area = [3, 5]
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
        )
        coords = weather.groupby(level=[1, 2]).mean().index
        assert len(coords) == 1
        print(coords)

    def test_level_drop_for_multi_coordinates(self):
        msg = "You cannot drop the coordinate levels if there are more than"
        with pytest.raises(ValueError, match=msg):
            weather_df_from_era5(
                era5_netcdf_filename=self.era5_netcdf_file,
                lib="windpowerlib",
                drop_coord_levels=True,
            )

    def test_keep_level_for_single_coordinate(self):
        lat_point_list = [52.35, 52.35, 52.65]
        lon_point_list = [13.0, 13.4, 13.4]
        area = Polygon(zip(lon_point_list, lat_point_list))
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
            drop_coord_levels=False,
        )
        assert isinstance(weather.index, pd.MultiIndex)

    def test_drop_level_for_single_coordinate(self):
        lat_point_list = [52.35, 52.35, 52.65]
        lon_point_list = [13.0, 13.4, 13.4]
        area = Polygon(zip(lon_point_list, lat_point_list))
        weather = weather_df_from_era5(
            era5_netcdf_filename=self.era5_netcdf_file,
            lib="windpowerlib",
            area=area,
            drop_coord_levels=True,
        )
        assert not isinstance(weather.index, pd.MultiIndex)
