#!/usr/bin/env python
# coding: utf-8

"""
This example shows you how to download ERA5 weather data from the
`Climate Data Store (CDS) <https://cds.climate.copernicus.eu>`_ and store it
locally.

In order to download ERA5 weather data you need an account at the
`CDS <https://cds.climate.copernicus.eu>`_.

Furthermore, you need to install the cdsapi package. See the howto for the
`api <https://cds.climate.copernicus.eu/api-how-to>`_ for installation details.

When downloading the data using the API your request gets queued and may take
a while to be completed.

Besides a location you have to specify a time period for which you would like
to download the data as well as the weather variables you need. The feedinlib
provides predefined sets of variables that are needed to use the pvlib and
windpowerlib. These can be applied by setting the `variable` parameter to
"pvlib" or "windpowerlib", as shown below. If you want to download data for
both libraries you can set `variable` to "feedinlib".

Concerning the start and end date, keep in mind that all timestamps in the
`feedinlib` are in UTC. So if you later on want to convert the data to a
different time zone, the data may not cover the whole period you intended to
download. To avoid this set your start date to one day before the start of
your required period if you are East of the zero meridian or your end date
to one day after your required period ends if you are West of the zero
meridian.
"""

import math
import multiprocessing
import os.path

from feedinlib import era5


def download_era5(parameters):
    era5.get_era5_data_from_datespan_and_position(
        variable=parameters.get("variable"),
        start_date=parameters.get("start_date"),
        end_date=parameters.get("end_date"),
        latitude=parameters.get("latitude"),
        longitude=parameters.get("longitude"),
        target_file=parameters.get("target_file"),
        chunks=parameters.get("chunks"),
    )


def download_era5_multiprocessing_examples():
    # Define the locations:
    example_data = os.path.join(os.path.dirname(__file__), "example_data")

    locations = [
        {
            "latitude": 54.16,
            "longitude": 9.08,
            "start_date": "2019-01-01",
            "end_date": "2019-12-31",
            "variable": "feedinlib",
            "target_file": os.path.join(
                example_data,
                "era5_feedinlib_54-16_9-08_2019-01-01_2019-12-31.nc",
            ),
        },
        {
            "latitude": 54.43,
            "longitude": 7.68,
            "start_date": "2019-01-01",
            "end_date": "2019-12-31",
            "variable": "windpowerlib",
            "target_file": os.path.join(
                example_data,
                "era5_windpowerlib_54-43_7-68_2019-01-01_2019-12-31.nc",
            ),
        },
    ]

    # Download the data sets in parallel
    maximal_number_of_cores = math.ceil(multiprocessing.cpu_count() * 0.5)
    p = multiprocessing.Pool(maximal_number_of_cores)
    p.map(download_era5, locations)
    p.close()


if __name__ == "__main__":
    download_era5_multiprocessing_examples()
