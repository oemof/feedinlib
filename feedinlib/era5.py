import os
from datetime import datetime, timedelta, date
from tempfile import mkstemp
import logging
import xarray as xr
import cdsapi

logger = logging.getLogger(__name__)


def _get_cds_data(
        dataset_name='reanalysis-era5-single-levels',
        target_file=None,
        chunks=None,
        cds_client=None,
        **cds_params):
    """Download data from the Climate Data Store (CDS)
    Requirements:
        - user account at https://cds.climate.copernicus.eu to use this function
        - cdsapi package installed (https://cds.climate.copernicus.eu/api-how-to)

    :param dataset_name: (str) short name of the dataset of the CDS. To find it, click on a dataset
    found in https://cds.climate.copernicus.eu/cdsapp#!/search?type=dataset and go under the
    ’Download data’ tab, then scroll down the page and click on ’Show API request’, the short
    name is the string on the 6th line after 'c.retrieve('
    :param target_file: (str) name of the file in which downloading the data locally
    :param chunks: (dict)
    :param cds_client: handle to CDS client (if none is provided, then it is created)
    :param cds_params: (dict) parameter to pass to the CDS request
    :return: CDS data in an xarray format
    """

    if cds_client is None:
        cds_client = cdsapi.Client()

    # Default request
    request = {
        'format': 'netcdf',
        'product_type': 'reanalysis',
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ],
    }

    # Add user provided cds parameters to the request dict
    request.update(cds_params)

    assert {'year', 'month', 'variable'}.issubset(request), \
        "Need to specify at least 'variable', 'year' and 'month'"

    # Send the data request to the server
    result = cds_client.retrieve(
        dataset_name,
        request,
    )

    # Create a file in a secure way if a target filename was not provided
    if target_file is None:
        fd, target_file = mkstemp(suffix='.nc')
        os.close(fd)

    logger.info(
        "Downloading request for {} variables to {}".format(len(request['variable']), target_file)
    )

    # Download the data in the target file
    result.download(target_file)

    # Extract the data from the target file
    answer = xr.open_dataset(target_file, chunks=chunks)

    # Now that the data has been extracted the file path is removed if it was not provided
    if target_file is None:
        os.unlink(target_file)

    return answer


def _format_cds_request_datespan(start_date, end_date):
    """Format the dates between two given dates in order to submit a CDS request

    :param start_date: (str) start date of the range in YYYY-MM-DD format
    :param end_date: (str) end date of the range in YYYY-MM-DD format
    :return: a dict with the years, months and days of all the dates as lists of string
    """

    answer = {'year': [], 'month': [], 'day': []}
    fmt = '%Y-%m-%d'
    start_dt = datetime.strptime(start_date, fmt)
    end_dt = datetime.strptime(end_date, fmt)

    if end_dt < start_dt:
        logger.warning(
            "Swapping input dates as the end date '{}' is prior to the start date '{}'.".format(
                end_date, start_date
            )
        )
        start_dt = end_dt
        end_dt = datetime.strptime(start_date, fmt)

    for n in range(int((end_dt - start_dt).days) + 1):
        cur_dt = start_dt + timedelta(n)

        # Add string value of the date's year, month and day to the corresponding lists in the
        # dict which will be returned
        for key, val in zip(['year', 'month', 'day'], [cur_dt.year, cur_dt.month, cur_dt.day]):
            val = str(val)
            if val not in answer[key]:
                answer[key].append(val)

    # If the datespan is over more than a month, then all days are filled and the entire months
    # are returned (for CDS request the days format for a full month is 31 days).
    if len(answer['month']) > 1:
        answer['day'] = [str(d) for d in range(1, 32, 1)]

    return answer


def _format_cds_request_position(latitude, longitude, grid=None):
    """Format the dates between two given dates in order to submit a CDS request

    :param latitude: (number)
    :param longitude: (number)
    :return: a list with North latitude, West longitude, South latitude, and East longitude
    """

    area = []
    answer = {}

    if grid is None:
        grid = [0.25, 0.25]

    if area:
        answer['area']: area

    return answer


def _get_cds_data_from_datespan_and_position(
        start_date,
        end_date,
        latitude,
        longitude,
        grid=None,
        dataset_name='reanalysis-era5-single-levels',
        target_file=None,
        chunks=None,
        cds_client=None,
        **cds_params):
    """Format request for data from the Climate Data Store (CDS)

        see _get_cds_data() for prior requirements and more information

    :param start_date: (str) start date of the range in YYYY-MM-DD format
    :param end_date: (str) end date of the range in YYYY-MM-DD format
    :param latitude: (number)
    :param longitude: (number)
    :param dataset_name: (str) short name of the dataset of the CDS. To find it, click on a dataset
    found in https://cds.climate.copernicus.eu/cdsapp#!/search?type=dataset and go under the
    ’Download data’ tab, then scroll down the page and click on ’Show API request’, the short
    name is the string on the 6th line after 'c.retrieve('
    :param target_file: (str) name of the file in which downloading the data locally
    :param chunks: (dict)
    :param cds_client: handle to CDS client (if none is provided, then it is created)
    :param cds_params: (dict) parameter to pass to the CDS request
    :return: CDS data in an xarray format
    """

    kwargs = locals()
    # Get the formatted year, month and day parameter from the datespan
    request_dates = _format_cds_request_datespan(start_date, end_date)
    cds_params.update(request_dates)
    # Get the area corresponding to a position on the globe for a given grid size
    request_area = _format_cds_request_position(latitude, longitude, grid)
    cds_params.update(request_area)
    # Remove the arguments which will not be passed to the _get_cds_data function
    kwargs.pop('start_date')
    kwargs.pop('end_date')
    kwargs.pop('longitude')
    kwargs.pop('latitude')
    kwargs.pop('grid')

    return _get_cds_data(**kwargs)

