import pandas as pd
import geopandas as gpd
from feedinlib.db_bs import Weather
from feedinlib.db_bs import defaultdb
import pickle
import os.path

from geoalchemy2.elements import WKTElement as WKTE
from itertools import chain
from shapely.ops import cascaded_union


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

    for nut_id in districts_shape.nuts.unique():
        tmp_df = districts_shape[districts_shape.nuts == nut_id]
        if len(tmp_df) > 1:
            polyg = cascaded_union(
                districts_shape[districts_shape.nuts == nut_id].geometry)
            counter = 0
            for index, row in tmp_df.iterrows():
                if counter == 0:
                    districts_shape.loc[index, 'geometry'] = polyg
                else:
                    districts_shape.drop(index=[index], inplace=True)
                counter += 1

    if dump_shape:
        districts_shape.to_file('districts_{}.shp'.format(state))
    return districts_shape


def make_weather_df_from_pkl_for_districts(
        state, year, server_path, dump_districts_shape=False):

    districts_df = get_districts_for_state(
        state, dump_shape=dump_districts_shape)

    for index, rows in districts_df.iterrows():

        weather_data_filename = 'weather_data_{}_{}.csv'.format(
            rows['nuts'], year)

        if not os.path.isfile(weather_data_filename):

            # get all location ids in district
            location_ids = get_location_ids_within_region(rows['geometry'])
            print('{}: number of location ids {}'.format(
                rows['nuts'], len(location_ids)))

            # first location
            fname = os.path.join(server_path,
                                 '{}_{}.pkl'.format(location_ids[0], year))
            open_FRED_weather = pickle.load(open(fname, "rb"))

            # all other locations
            for location in location_ids[1:]:
                fname = os.path.join(
                    server_path, '{}_{}.pkl'.format(location, year))
                tmp_data = pickle.load(open(fname, "rb"))

                open_FRED_weather.series.update(tmp_data.series)
                open_FRED_weather.variables.update(tmp_data.variables)

            open_FRED_weather.df().to_csv(weather_data_filename)


def make_weather_object_from_dumped_csv(district, state):

    df = pd.read_csv('weather_data_{}.csv'.format(district))
    open_FRED_weather = Weather.from_df(df)

    # test if it worked:
    # load locations dict with location ids and corresponding coordinates
    locations_dict = pickle.load(
        open("locations_dict_{}.pkl".format(state), "rb"))

    location = list(locations_dict.keys())[0]
    open_FRED_weather.df(
        location=locations_dict[location],
        lib='pvlib')


if __name__ == "__main__":

    server_path = '/home/birgit/rli-daten/open_FRED_Wetterdaten_pkl'
    # years 2013 - 2017
    year = 2017
    state = 'Mecklenburg-Vorpommern'  # 'Mecklenburg-Vorpommern', 'Sachsen', 'Brandenburg', 'Sachsen-Anhalt', 'Thüringen', 'Berlin'

    shape_df = gpd.read_file('germany.geojson')
    shape = shape_df[shape_df.name == state].loc[:, 'geometry'].values[0]

    #download_and_dump_weather_data(shape, state, year, server_path)

    #get_districts_for_state(state, dump_shape=True)

    make_weather_df_from_pkl_for_districts(state, year, server_path,
                                           dump_districts_shape=False)
