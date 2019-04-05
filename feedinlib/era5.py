from cds_request_tools import get_cds_data_from_datespan_and_position


def get_era5_data_from_datespan_and_position(
        start_date,
        end_date,
        latitude,
        longitude,
        grid=None,
        target_file=None,
        chunks=None,
        cds_client=None,
        **cds_params
):
    """Send request for era5 data from the Climate Data Store (CDS)

    :param start_date: (str) start date of the range in YYYY-MM-DD format
    :param end_date: (str) end date of the range in YYYY-MM-DD format
    :param latitude: (number) latitude in the range [-90, 90] referenced to the equator,
        north correspond to positive latitude.
    :param longitude: (number) longitude in the range [-180, 180] referenced to Greenwich
        Meridian, east relative to the meridian correspond to positive longitude.
    :param grid: (list of float) provide the latitude and longitude grid resolutions in deg. It
    needs to be an integer fraction of 90 deg.
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

    dataset_name = 'reanalysis-era5-single-levels'
    variable = '2m_temperature'
    return get_cds_data_from_datespan_and_position(**locals())


def get_pvlib_timeseries_data(
        start_date,
        end_date,
        latitude,
        longitude
):
    """Fetch pvlib data from era5 database in the Climate Data Store (CDS)
    https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview

    :param start_date: (str) start date of the range in YYYY-MM-DD format
    :param end_date: (str) end date of the range in YYYY-MM-DD format
    :param latitude: (number) latitude in the range [-90, 90] referenced to the equator,
        north correspond to positive latitude.
    :param longitude: (number) longitude in the range [-180, 180] referenced to Greenwich
        Meridian, east relative to the meridian correspond to positive longitude.
    :return: CDS data in an xarray format
    """
    # Define the variable needed from the database
    # wind speed, air temperature, global horizontal irradiance (GHI),
    # diffuse horizontal irradiance (DHI), direct normal irradiance (DNI)
    variable = []
    grid = []

    return get_era5_data_from_datespan_and_position(**locals())


def get_windpowerlib_timeseries_data(
        start_date,
        end_date,
        latitude,
        longitude
):
    """Fetch windpowerlib data from era5 database in the Climate Data Store (CDS)
    https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview

    :param start_date: (str) start date of the range in YYYY-MM-DD format
    :param end_date: (str) end date of the range in YYYY-MM-DD format
    :param latitude: (number) latitude in the range [-90, 90] referenced to the equator,
        north correspond to positive latitude.
    :param longitude: (number) longitude in the range [-180, 180] referenced to Greenwich
        Meridian, east relative to the meridian correspond to positive longitude.
    :return: CDS data in an xarray format
    """
    # Define the variable needed from the database
    # wind speed, air temperature, air pressure, roughness length
    variable = []
    grid = []

    return get_era5_data_from_datespan_and_position(**locals())

