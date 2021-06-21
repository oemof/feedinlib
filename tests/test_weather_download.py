from feedinlib import era5
import cdsapi
from unittest import mock


def test_era5_download():
    cdsapi.Client = mock.Mock()
    instance_of_client = cdsapi.Client.return_value
    instance_of_client.download.return_value = None
    era5.get_era5_data_from_datespan_and_position(
        "2019-01-19", "2019-01-20", "test_file.nc", "50.0", "12.0"
    )
