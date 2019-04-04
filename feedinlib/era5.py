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

    dataset_name = 'reanalysis-era5-single-levels',

    return get_cds_data_from_datespan_and_position(**locals())
