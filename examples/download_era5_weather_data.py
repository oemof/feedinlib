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

import os.path

from feedinlib import era5


def download_era5(**kwargs):
    if kwargs.get("target_file") is None:
        target_file = (
            ("era5_{variable}_{latitude}_{longitude}_{start_date}_{end_date}_"
             "{chunks}")
            .format(**kwargs)
            .replace(".", "-")
            .replace(", ", "_")
            .replace("_None", "")
        )
    else:
        target_file = kwargs.get("target_file")

    if kwargs.get("path") is not None:
        target_file = os.path.join(kwargs.get("path"), target_file)

    if not os.path.isfile(target_file) or kwargs.get("overwrite", False):
        era5.get_era5_data_from_datespan_and_position(
            variable=kwargs.get("variable"),
            start_date=kwargs.get("start_date"),
            end_date=kwargs.get("end_date"),
            latitude=kwargs.get("latitude"),
            longitude=kwargs.get("longitude"),
            target_file=target_file,
            chunks=kwargs.get("chunks"),
        )


# Download a single coordinate for the year 2019 with all variables
single_coord = {
    "latitude": 54.16,
    "longitude": 9.08,
    "start_date": "2019-01-01",
    "end_date": "2019-12-31",
    "variable": "feedinlib",
}
download_era5(**single_coord)

# Download a single coordinate for the year 2019 with windpowerlib variables
single_coord = {
    "latitude": 54.43,
    "longitude": 7.68,
    "start_date": "2019-01-01",
    "end_date": "2019-12-31",
    "variable": "windpowerlib",
}
download_era5(**single_coord)

# When wanting to download weather data for a region you have to provide a
# bounding box with latitude and longitude as lists.
bb_coord = {
    "latitude": [52.3, 52.7],  # [latitude south, latitude north]
    "longitude": [13.1, 13.6],  # [longitude west, longitude east]
    "start_date": "2017-01-01",
    "end_date": "2017-12-31",
    "variable": "pvlib",
    "target_file": "ERA5_berlin_feedinlib_example_2017.nc",
}
download_era5(**bb_coord)

# Download all coordinates of the world for one year
world = {
    "variable": "feedinlib",
    "start_date": "2017-01-01",
    "end_date": "2017-12-31",
    "target_file": "ERA5_world_feedinlib_2017.nc",
}
download_era5(**world)
