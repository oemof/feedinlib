import geopandas as gpd
from feedinlib.db_bs import Weather
from feedinlib.db_bs import defaultdb
import pickle
import os.path

from geoalchemy2.elements import WKTElement as WKTE
from itertools import chain


def within(region=None):
    """ Get all measurement locations within the given `region`.
    """
    region = WKTE(region.to_wkt(), srid=4326)
    session_dict = defaultdb()
    return (
        session_dict['session'].query(session_dict['db']["Location"])
            .filter(session_dict['db']["Location"].point.ST_Within(region))
            .all()
    )


def get_location_ids_within_region(region_shape):
    regions = {WKTE(r, srid=4326): within(r) for r in [region_shape]}
    location_ids = [l.id for l in chain(*regions.values())]
    return location_ids


def download_and_dump_weather_data(region_shape, state, year, server_path):
    location_ids = get_location_ids_within_region(region_shape)

    start_date, end_date = '{}-01-01'.format(year), '{}-01-01'.format(year+1)

    # locations dictionary
    fname_loc = os.path.join(server_path, "locations_dict_{}.pkl".format(
        state))
    if os.path.isfile(fname_loc):
        locations_dict = pickle.load(open(fname_loc, "rb"))
    else:
        locations_dict = {}

    for location in location_ids:
        print("location: {}".format(location))
        fname = os.path.join(server_path, '{}_{}.pkl'.format(location, year))
        if not os.path.isfile(fname):
            open_FRED_weather = Weather(
                start_date, end_date, [location],
                heights=None,
                variables="windpowerlib",
                **defaultdb())
            open_FRED_weather.session = None
            open_FRED_weather.db = None
            pickle.dump(open_FRED_weather, open(fname, 'wb'))
            locations_dict[location] = list(
                open_FRED_weather.series.keys())[0][0]
            pickle.dump(locations_dict, open(fname_loc, 'wb'))


def get_districts_for_state(state, dump_shape=False):
    """
    Returns geopandas dataframe with columns nuts and geometry for all
    districts in given state.

    """
    nuts_id = {
        'Mecklenburg-Vorpommern': 'DE80',
        'Sachsen': 'DED2',
        'Brandenburg': 'DE40',
        'Sachsen-Anhalt': 'DEE0',
        'Thüringen': 'DEG0',
        'Berlin': 'DE30'
    }
    file = '/home/birgit/rli-server/04_Projekte/163_Open_FRED/' \
           '03-Projektinhalte/AP7 Community/paper_data/' \
           'geometries/Landkreise/landkreise_dump.shp'

    landkreise_shape = gpd.read_file(file)
    districts_shape = landkreise_shape[
        landkreise_shape.nuts.str.contains(nuts_id[state])]
    if dump_shape:
        districts_shape.to_file('districts_{}.shp'.format(state))
    return districts_shape


def make_weather_df_from_pkl_for_districts(state, dump_districts_shape=False):

    districts_df = get_districts_for_state(
        state, dump_shape=dump_districts_shape)

    for district in districts_df.iterrows():

        # get all location ids in district
        locations_dict = get_location_ids_within_region(district.geometry)

        location_ids = locations_dict.keys()
        pickle_dict = {}
        for location in location_ids:
            pickle_dict[location] = pickle.load(
                open("{}.pkl".format(location), "rb"))

        open_FRED_weather = pickle_dict[location_ids[0]]
        for location in location_ids[1:]:
            open_FRED_weather.series.update(pickle_dict[location].series)
            open_FRED_weather.variables.update(pickle_dict[location].variables)

    # # load locations dict with location ids and corresponding coordinates
    # locations_dict = pickle.load(
    #     open("locations_dict_{}.pkl".format(state), "rb"))
    #
    # location = list(locations_dict.keys())[0]
    # open_FRED_weather.df(
    #     location=locations_dict[location],
    #     lib='pvlib')


if __name__ == "__main__":

    server_path = ''
    # years 2013 - 2017
    year = 2017
    state = 'Mecklenburg-Vorpommern'  # 'Mecklenburg-Vorpommern', 'Sachsen', 'Brandenburg', 'Sachsen-Anhalt', 'Thüringen', 'Berlin'

    shape_df = gpd.read_file('germany.geojson')
    shape = shape_df[shape_df.name == state].loc[:, 'geometry'].values[0]

    #download_and_dump_weather_data(shape, state, year, server_path)

    make_weather_df_from_pkl_for_districts(state, dump_districts_shape=False)
