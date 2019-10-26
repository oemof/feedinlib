import geopandas as gpd
from feedinlib.db_bs import Weather
from feedinlib.db_bs import defaultdb
import pickle
import os.path

# years 2013 - 2017

year = 2017
state = 'Brandenburg'

shape_df = gpd.read_file('germany.geojson')
shape = shape_df[shape_df.name==state].loc[:, 'geometry'].values[0]

# get location IDs
from geoalchemy2.elements import WKTElement as WKTE
from itertools import chain
session_dict = defaultdb()

def within(region=None):
    """ Get all measurement locations within the given `region`.
    """
    region = WKTE(region.to_wkt(), srid=4326)
    return (
        session_dict['session'].query(session_dict['db']["Location"])
            .filter(session_dict['db']["Location"].point.ST_Within(region))
            .all()
    )

regions = {WKTE(r, srid=4326): within(r) for r in [shape]}
location_ids = [l.id for l in chain(*regions.values())]

start_date, end_date = '{}-01-01'.format(year), '{}-01-01'.format(year+1)

# locations dictionary
fname_loc = "locations_dict_{}.pkl".format(state)
if os.path.isfile(fname_loc):
    locations_dict = pickle.load(open(fname_loc, "rb"))
else:
    locations_dict = {}

for location in location_ids:
    print("location: {}".format(location))
    fname = '{}_{}.pkl'.format(location, year)
    if not os.path.isfile(fname):
        open_FRED_weather = Weather(
            start_date, end_date, [location],
            heights=None,
            variables="windpowerlib",
            **defaultdb())
        open_FRED_weather.session = None
        open_FRED_weather.db = None
        pickle.dump(open_FRED_weather, open(fname, 'wb'))
        locations_dict[location] = list(open_FRED_weather.series.keys())[0][0]
        pickle.dump(locations_dict, open(fname_loc, 'wb'))

# # read pickle
# print("read pickle")
# locations_dict = pickle.load(open("locations_dict.pkl", "rb" ))
# pickle_dict = {}
# for location in locations:
#     pickle_dict[location] = pickle.load(
#         open("{}.pkl".format(location), "rb" ))
#
# open_FRED_weather = pickle_dict[locations[0]]
# open_FRED_weather.series.update(pickle_dict[locations[1]].series)
# open_FRED_weather.variables.update(pickle_dict[locations[1]].variables)
#
# print()
# location = list(locations_dict.keys())[1]
# open_FRED_weather.df(
#     location=locations_dict[location],
#     lib='pvlib')
# location = list(locations_dict.keys())[0]
# open_FRED_weather.df(
#     location=locations_dict[location],
#     lib='pvlib')
#
# print(time.time())