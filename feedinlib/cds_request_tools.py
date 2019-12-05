import os
from datetime import datetime, timedelta
from tempfile import mkstemp
import logging
import numpy as np
import xarray as xr
import cdsapi

logger = logging.getLogger(__name__)


def _get_cds_data(
    dataset_name="reanalysis-era5-single-levels",
    target_file=None,
    chunks=None,
    cds_client=None,
    **cds_params
):
    """
    Download data from the Climate Data Store (CDS)

    Requirements:
    * user account at https://cds.climate.copernicus.eu to use this function
    * cdsapi package installed (https://cds.climate.copernicus.eu/api-how-to)

    :param dataset_name: (str) short name of the dataset of the CDS. To find
        it, click on a dataset found in
        https://cds.climate.copernicus.eu/cdsapp#!/search?type=dataset and go
        to the 'Download data' tab, then scroll down the page and click on
        'Show API request', the short name is the string on the 6th line
        after 'c.retrieve('
    :param target_file: (str) name of the file to save downloaded locally
    :param chunks: (dict)
    :param cds_client: handle to CDS client (if none is provided, then it is
        created)
    :param cds_params: (dict) parameter to pass to the CDS request

    :return: CDS data in an xarray format

    """

    # https://cds.climate.copernicus.eu/api-how-to
    if cds_client is None:
        cds_client = cdsapi.Client()

    # Default request
    request = {
        "format": "netcdf",
        "product_type": "reanalysis",
        "time": [
            "00:00",
            "01:00",
            "02:00",
            "03:00",
            "04:00",
            "05:00",
            "06:00",
            "07:00",
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
            "19:00",
            "20:00",
            "21:00",
            "22:00",
            "23:00",
        ],
    }

    # Add user provided cds parameters to the request dict
    request.update(cds_params)

    assert {"year", "month", "variable"}.issubset(
        request
    ), "Need to specify at least 'variable', 'year' and 'month'"

    # Send the data request to the server
    result = cds_client.retrieve(dataset_name, request,)

    no_target_file_provided = target_file is None
    # Create a file in a secure way if a target filename was not provided
    if no_target_file_provided is True:
        fd, target_file = mkstemp(suffix=".nc")
        os.close(fd)

    logger.info(
        "Downloading request for {} variables to {}".format(
            len(request["variable"]), target_file
        )
    )

    # Download the data in the target file
    result.download(target_file)

    # Extract the data from the target file
    answer = xr.open_dataset(target_file, chunks=chunks)

    # Now that the data has been extracted the file path is removed if it was
    # not provided. This will currently not work on windows if the dataset is
    # too large as the file will be locked by the reading process.
    if no_target_file_provided is True:
        os.unlink(target_file)

    # Here yield might be preferable in case of large datasets
    return answer


def _format_cds_request_datespan(start_date, end_date):
    """
    Format the dates between two given dates in order to submit a CDS request

    :param start_date: (str) start date of the range in YYYY-MM-DD format
    :param end_date: (str) end date of the range in YYYY-MM-DD format

    :return: a dict with the years, months and days of all the dates as lists
        of string

    """

    answer = {"year": [], "month": [], "day": []}
    fmt = "%Y-%m-%d"
    specific_fmt = {"year": "%4d", "month": "%02d", "day": "%02d"}
    start_dt = datetime.strptime(start_date, fmt)
    end_dt = datetime.strptime(end_date, fmt)

    if end_dt < start_dt:
        logger.warning(
            "Swapping input dates as the end date '{}' is prior to the "
            "start date '{}'.".format(end_date, start_date)
        )
        start_dt = end_dt
        end_dt = datetime.strptime(start_date, fmt)

    for n in range(int((end_dt - start_dt).days) + 1):
        cur_dt = start_dt + timedelta(n)

        # Add string value of the date's year, month and day to the
        # corresponding lists in the dict which will be returned
        for key, val in zip(
            ["year", "month", "day"], [cur_dt.year, cur_dt.month, cur_dt.day]
        ):
            val = specific_fmt[key] % val
            if val not in answer[key]:
                answer[key].append(val)

    # If the datespan is over more than a month, then all days are filled and
    # the entire months are returned (for CDS request the days format for a
    # full month is 31 days).
    if len(answer["month"]) > 1:
        answer["day"] = [str(d) for d in range(1, 32, 1)]

    return answer


def _format_cds_request_area(
    latitude_span=None, longitude_span=None, grid=None
):
    """
    Format the area between two given latitude and longitude spans in order
    to submit a CDS request

    The grid convention of the era5 HRES is used with a native resolution of
    0.28125 deg. For NetCDF format, the data is interpolated to a regular
    lat/lon grid with 0.25 deg resolution.
    In this grid the earth is modelled by a sphere with radius
    R_E = 6367.47 km. Latitude values in the range [-90, 90] relative to the
    equator and longitude values in the range [-180, 180]
    relative to the Greenwich Prime Meridian [1].

    References:
    [1] https://confluence.ecmwf.int/display/CKB/ERA5%3A+What+is+the+spatial+reference
    [2] https://confluence.ecmwf.int/display/UDOC/Post-processing+keywords

    :param latitude_span: (list of float) formatted as [N,S]. The span is
        between North and South latitudes (relative to the equator). North
        corresponds to positive latitude [2].
    :param longitude_span: (list of float) formatted as [W,E]. The span is
        between East and West longitudes (relative to the Greenwich meridian).
        East corresponds to positive longitude [2].
    :param grid: (list of float) provide the latitude and longitude grid
        resolutions in deg. It needs to be an integer fraction of 90 deg [2].

    :return: a dict containing the grid and, if `latitude_span` and/or
        `longitude_span` were specified, the area formatted for a CDS request

    """

    answer = {}

    # Default value of the grid
    if grid is None:
        grid = [0.25, 0.25]

    if latitude_span is not None and longitude_span is not None:
        area = [
            latitude_span[0],
            longitude_span[0],
            latitude_span[1],
            longitude_span[1],
        ]
    elif latitude_span is None and longitude_span is not None:
        area = [90, longitude_span[0], -90, latitude_span[1]]
    elif latitude_span is not None and longitude_span is None:
        area = [latitude_span[0], -180, latitude_span[1], 180]
    else:
        area = []

    # Format the 'grid' keyword of the CDS request as
    # lat_resolution/lon_resolution
    answer["grid"] = "%.2f/%.2f" % (grid[0], grid[1])

    # Format the 'area' keyword of the CDS request as N/W/S/E
    if area:
        answer["area"] = "/".join(str(e) for e in area)

    return answer


def _format_cds_request_position(latitude, longitude, grid=None):
    """
    Reduce the area of a CDS request to a single GIS point on the earth grid

    Find the closest grid point for the given longitude and latitude.

    The grid convention of the era5 HRES is used here with a native
    resolution of 0.28125 deg. For NetCDF format the data is interpolated to a
    regular lat/lon grid with 0.25 deg resolution. In this grid the earth is
    modelled by a sphere with radius R_E = 6367.47 km. latitude values
    in the range [-90, 90] relative to the equator and longitude values in the
    range [-180, 180] relative to the Greenwich Prime Meridian [1].

    References:
    [1] https://confluence.ecmwf.int/display/CKB/ERA5%3A+What+is+the+spatial+reference
    [2] https://confluence.ecmwf.int/display/UDOC/Post-processing+keywords

    :param latitude: (number) latitude in the range [-90, 90] relative to the
        equator, north correspond to positive latitude.
    :param longitude: (number) longitude in the range [-180, 180] relative to
        Greenwich Meridian, east relative to the meridian correspond to
        positive longitude.
    :param grid: (list of float) provide the latitude and longitude grid
        resolutions in deg. It needs to be an integer fraction of 90 deg [2].

    :return: a dict containing the grid and the area formatted for a CDS
        request

    """

    # Default value of the grid
    if grid is None:
        grid = [0.25, 0.25]

    # Find the nearest point on the grid corresponding to the given latitude
    # and longitude
    grid_point = xr.Dataset(
        {
            "lat": np.arange(90, -90, -grid[0]),
            "lon": np.arange(-180, 180.0, grid[1]),
        }
    ).sel(lat=latitude, lon=longitude, method="nearest")

    # Prepare an area which consists of only one grid point
    lat, lon = [float(grid_point.coords[s]) for s in ("lat", "lon")]
    return _format_cds_request_area(
        latitude_span=[lat, lat], longitude_span=[lon, lon], grid=grid
    )


def get_cds_data_from_datespan_and_position(
    start_date,
    end_date,
    latitude=None,
    longitude=None,
    grid=None,
    **cds_params
):
    """
    Format request for data from the Climate Data Store (CDS)

    prepare a CDS request from user specified date span for a single grid point
    closest to the specified latitude and longitude.

    see _get_cds_data() for prior requirements and more information

    :param start_date: (str) start date of the datespan in YYYY-MM-DD format
    :param end_date: (str) end date of the datespan in YYYY-MM-DD format
    :param latitude: (number or list of float or None)
        * number: latitude in the range [-90, 90] relative to the
        equator, north correspond to positive latitude.
        * list of float: must be formatted as [N,S]. The span is
        between North and South latitudes (relative to the equator). North
        corresponds to positive latitude.
        * None: No geographical subset is selected.
    :param longitude: (number or list of float or None)
        * number: longitude in the range [-180, 180] relative to
        Greenwich Meridian, east relative to the meridian correspond to
        positive longitude.
        * list of float: must be formatted as [W,E]. The span is
        between East and West longitudes (relative to the Greenwich meridian).
        East corresponds to positive longitude
        * None: No geographical subset is selected.
    :param grid: (list of float) provide the latitude and longitude grid
        resolutions in deg. It needs to be an integer fraction of 90 deg.
    :param dataset_name: (str) short name of the dataset of the CDS. To find
        it, click on a dataset found in
        https://cds.climate.copernicus.eu/cdsapp#!/search?type=dataset and go
        to the 'Download data' tab, then scroll down the page and click on
        'Show API request', the short name is the string on the 6th line
        after 'c.retrieve('
    :param target_file: (str) name of the file in which downloading the data
        locally
    :param chunks: (dict)
    :param cds_client: handle to CDS client (if none is provided, then it is
        created)
    :param cds_params: (dict) parameter to pass to the CDS request

    :return: CDS data in an xarray format

    """

    # Get the formatted year, month and day parameter from the datespan
    request_dates = _format_cds_request_datespan(start_date, end_date)
    cds_params.update(request_dates)

    # Get the area corresponding to a position on the globe for a given grid
    # size
    # if both longitude and latitude are provided as number, select single
    # position
    if isinstance(longitude, (int, float)) or isinstance(
        latitude, (int, float)
    ):
        request_area = _format_cds_request_position(latitude, longitude, grid)
        cds_params.update(request_area)
    # if longitude or latitude is provided as list and the other one is either
    # None (in which case all latitudes or longitudes are selected) or also
    # provided as list, select area
    elif isinstance(longitude, list) or isinstance(latitude, list):
        if not isinstance(longitude, (int, float)) and not isinstance(
            latitude, (int, float)
        ):
            request_area = _format_cds_request_area(latitude, longitude, grid)
            cds_params.update(request_area)
        else:
            raise ValueError(
                "It is currently not supported that latitude or longitude is "
                "provided as a number while the other is provided as a list."
            )
    # in any other case no geographical subset is selected

    return _get_cds_data(**cds_params)
