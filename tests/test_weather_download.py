from unittest import mock

import cdsapi
import pandas as pd
import pytest

from feedinlib import era5
from feedinlib.era5 import weather_df_from_era5


def test_era5_download():
    cdsapi.Client = mock.Mock()
    instance_of_client = cdsapi.Client.return_value
    instance_of_client.download.return_value = None
    era5.get_era5_data_from_datespan_and_position(
        "2019-01-19", "2019-01-20", "test_file.nc", "50.0", "12.0"
    )


def test_get_weather_df_from_era5():
    era5_netcdf_filename = "resources/test_data_era5.nc"

    df = weather_df_from_era5(era5_netcdf_filename, lib='pvlib')

    expected_val = -3.808929
    actual_val = df.loc[(pd.Timestamp("2004-01-01 03:30:00+00:00"), 53.0, 8.75), "temp_air"]

    assert actual_val == pytest.approx(expected_val, rel=1e-5)
