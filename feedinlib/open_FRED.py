from itertools import chain, groupby
from numbers import Number

from pandas import DataFrame as DF, Series, Timedelta as TD, to_datetime as tdt
from geoalchemy2.elements import WKTElement as WKTE
from geoalchemy2.shape import to_shape
from shapely.geometry import Point
from sqlalchemy.orm import sessionmaker
import oedialect
import pandas as pd
import sqlalchemy as sqla

import open_FRED.cli as ofr


TRANSLATIONS = {
    "windpowerlib": {
        "wind_speed": [("VABS_AV",)],
        "temperature": [("T",)],
        "roughness_length": [("Z0",)],
        "pressure": [("P",)],
    },
    "pvlib": {
        "wind_speed": [("VABS_AV", 10)],
        "temp_air": [("T", 10)],
        "pressure": [("P", 10)],
        "dhi": [("ASWDIFD_S", 0)],
        "ghi": [("ASWDIFD_S", 0), ("ASWDIR_S", 0)],
        "dni": [("ASWDIRN_S", 0)],
    },
}


def defaultdb():
    engine = getattr(defaultdb, "engine", None) or sqla.create_engine(
        "postgresql+oedialect://openenergy-platform.org"
    )
    defaultdb.engine = engine
    session = (
        getattr(defaultdb, "session", None) or sessionmaker(bind=engine)()
    )
    defaultdb.session = session
    metadata = sqla.MetaData(schema="model_draft", bind=engine, reflect=False)
    return {"session": session, "db": ofr.mapped_classes(metadata)}


class Weather:
    """
    Load weather measurements from an openFRED conforming database.

    Note that you need a database storing weather data using the openFRED
    schema in order to use this class. There is one publicly available at

        https://openenergy-platform.org

    Now you can simply instantiate a `Weather` object via e.g.:

    >>> from shapely.geometry import Point
    >>> point = Point(9.7311, 53.3899)
    >>> weather = Weather(
    ...    "2003-04-05 06:00",
    ...    "2003-04-05 07:31",
    ...    [point],
    ...    [10],
    ...    "pvlib",
    ...    **defaultdb()
    ...)

    Instead of the special values `"pvlib"` and `"windpowerlib"` you can
    also supply a list of variables, like e.g. `["P", "T", "Z0"]`, to
    retrieve from the database.

    After initialization, you can use e.g. `weather.df(point, "pvlib")`
    to retrieve a `DataFrame` with weather data from the measurement
    location closest to the given `point`.

    Parameters
    ----------
    start : Anything `pandas.to_datetime` can convert to a timestamp
        Load weather data starting from this date.
    stop : Anything `pandas.to_datetime` can convert to a timestamp
        Don't load weather data before this date.
    locations : list of :shapely:`Point`
        Weather measurements are collected from measurement locations closest
        to the the given points.
    heights : list of numbers
        Limit selected timeseries to these heights. If `variables` contains a
        variable which isn't height dependent, i.e. it has only one height,
        namely `0`, the corresponding timeseries is always
        selected. Don't select the correspoding variable, in order to avoid
        this.
        Defaults to `None` which means no restriction on height levels.
    variables : list of str or one of "pvlib" or "windpowerlib"
        Load the weather variables specified in the given list, or the
        variables necessary to calculate a feedin using `"pvlib"` or
        `"windpowerlib"`.
        Defaults to `None` which means no restriction on loaded variables.
    regions : list of :shapely:`Polygon`
         Weather measurements are collected from measurement locations
         contained within the given polygons.
    session : `sqlalchemy.orm.Session`
    db : dict of mapped classes

    """

    def __init__(
        self,
        start,
        stop,
        locations,
        heights=None,
        variables=None,
        regions=None,
        session=None,
        db=None,
    ):
        self.session = session
        self.db = db

        if self.session is None and self.db is None:
            return

        variables = {
            "windpowerlib": ["P", "T", "VABS_AV", "Z0"],
            "pvlib": [
                "ASWDIFD_S",
                "ASWDIRN_S",
                "ASWDIR_S",
                "P",
                "T",
                "VABS_AV",
            ],
            None: variables,
        }[variables if variables in ["pvlib", "windpowerlib"] else None]

        self.locations = (
            {(l.x, l.y): self.location(l) for l in locations}
            if locations is not None
            else {}
        )

        self.regions = (
            {WKTE(r, srid=4326): self.within(r) for r in regions}
            if regions is not None
            else {}
        )

        location_ids = [
            l.id
            for l in chain(self.locations.values(), *self.regions.values())
        ]

        self.locations = {
            k: to_shape(self.locations[k].point) for k in self.locations
        }
        self.locations.update(
            {
                (p.x, p.y): p
                for p in chain(
                    self.locations.values(),
                    (
                        to_shape(location.point)
                        for region in self.regions.values()
                        for location in region
                    ),
                )
            }
        )

        self.regions = {
            k: [to_shape(location.point) for location in self.regions[k]]
            for k in self.regions
        }

        series = sorted(
            session.query(
                db["Series"], db["Variable"], db["Timespan"], db["Location"]
            )
            .join(db["Series"].variable)
            .join(db["Series"].timespan)
            .join(db["Series"].location)
            .filter((db["Series"].location_id.in_(location_ids)))
            .filter(
                None
                if variables is None
                else db["Variable"].name.in_(variables)
            )
            .filter(
                None
                if heights is None
                else (db["Series"].height.in_(chain([0], heights)))
            )
            .filter(
                (db["Timespan"].stop >= tdt(start))
                & (db["Timespan"].start <= tdt(stop))
            )
            .all(),
            key=lambda p: (
                p[3].id,
                p[1].name,
                p[0].height,
                p[2].start,
                p[2].stop,
            ),
        )

        self.series = {
            k: [
                (
                    segment_start.tz_localize("UTC")
                    if segment_start.tz is None
                    else segment_start,
                    segment_stop.tz_localize("UTC")
                    if segment_stop.tz is None
                    else segment_stop,
                    value,
                )
                for (series, variable, timespan, location) in g
                for (segment, value) in zip(timespan.segments, series.values)
                for segment_start in [tdt(segment[0])]
                for segment_stop in [tdt(segment[1])]
                if segment_start >= tdt(start) and segment_stop <= tdt(stop)
            ]
            for k, g in groupby(
                series,
                key=lambda p: (
                    (to_shape(p[3].point).x, to_shape(p[3].point).y),
                    p[1].name,
                    p[0].height,
                ),
            )
        }
        # TODO: Fix the data. If possible add a constraint preventing this from
        #       happending again alongside the fix.
        #       This is just here because there's duplicate data (that we know)
        #       at the end of 2017. The last timestamp of 2017 is duplicated in
        #       the first timespan of 2018. And unfortunately it's not exactly
        #       duplicated. The timestamps are equal, but the values are only
        #       equal within a certain margin.
        self.series = {
            k: (
                self.series[k][:-1]
                if (self.series[k][-1][0:2] == self.series[k][-2][0:2])
                and (
                    (self.series[k][-1][2] == self.series[k][-2][2])
                    or (
                        isinstance(self.series[k][-1][2], Number)
                        and isinstance(self.series[k][-2][2], Number)
                        and (
                            abs(self.series[k][-1][2] - self.series[k][-2][2])
                            <= 0.5
                        )
                    )
                )
                else self.series[k]
            )
            for k in self.series
        }
        # TODO: Collect duplication errors not cought by the code above.

        self.variables = {
            k: sorted(set(h for _, h in g))
            for k, g in groupby(
                sorted((name, height) for _, name, height in self.series),
                key=lambda p: p[0],
            )
        }
        self.variables = {k: {"heights": v} for k, v in self.variables.items()}

    @classmethod
    def from_df(klass, df):
        assert isinstance(df.columns, pd.MultiIndex), (
            "DataFrame's columns aren't a `pandas.indexes.multi.MultiIndex`.\n"
            "Got `{}` instead."
        ).format(type(df.columns))
        assert len(df.columns.levels) == 2, (
            "DataFrame's columns have more than two levels.\nGot: {}.\n"
            "Should be exactly two, the first containing variable names and "
            "the\n"
            "second containing matching height levels."
        )
        variables = {
            variable: {"heights": [vhp[1] for vhp in variable_height_pairs]}
            for variable, variable_height_pairs in groupby(
                df.columns.values,
                key=lambda variable_height_pair: variable_height_pair[0],
            )
        }
        locations = {xy: Point(xy[0], xy[1]) for xy in df.index.values}
        series = {
            (xy, *variable_height_pair): df.loc[xy, variable_height_pair]
            for xy in df.index.values
            for variable_height_pair in df.columns.values
        }
        instance = klass(start=None, stop=None, locations=None)
        instance.locations = locations
        instance.series = series
        instance.variables = variables
        return instance

    def location(self, point: Point):
        """ Get the measurement location closest to the given `point`.
        """
        point = WKTE(point.to_wkt(), srid=4326)
        return (
            self.session.query(self.db["Location"])
            .order_by(self.db["Location"].point.distance_centroid(point))
            .first()
        )

    def within(self, region=None):
        """ Get all measurement locations within the given `region`.
        """
        region = WKTE(region.to_wkt(), srid=4326)
        return (
            self.session.query(self.db["Location"])
            .filter(self.db["Location"].point.ST_Within(region))
            .all()
        )

    def to_csv(self, path):
        df = self.df()
        df = df.applymap(
            # Unzip, i.e. convert a list of tuples to a tuple of lists, the
            # list of triples in each DataFrame cell and convert the result to
            # a JSON string. Unzipping is necessary because the pandas'
            # `to_json` wouldn't format the `Timestamps` correctly otherwise.
            lambda s: pd.Series(pd.Series(xs) for xs in zip(*s)).to_json(
                date_format="iso"
            )
        )
        return df.to_csv(path, quotechar="'")

    @classmethod
    def from_csv(cls, path_or_buffer):
        df = pd.read_csv(
            path_or_buffer,
            # This is necessary because the automatic conversion isn't precise
            # enough.
            converters={0: float, 1: float},
            header=[0, 1],
            index_col=[0, 1],
            quotechar="'",
        )
        df.columns.set_levels(
            [df.columns.levels[0], [float(l) for l in df.columns.levels[1]]],
            inplace=True,
        )
        df = df.applymap(lambda s: pd.read_json(s, typ="series"))
        # Reading the JSON string back in yields a weird format. Instead of a
        # nested `Series` we get a `Series` containing three dictionaries. The
        # `dict`s "emulate" a `Series` since their keys are string
        # representations of integers and their values are the actual values
        # that would be stored at the corresponding position in a `Series`. So
        # we have to manually reformat the data we get back. Since there's no
        # point in doing two conversions, we don't convert it back to nested
        # `Series`, but immediately to `list`s of `(start, stop, value)`
        # triples.
        df = df.applymap(
            lambda s: list(
                zip(
                    *[
                        [
                            # The `Timestamp`s in the inner `Series`/`dict`s
                            # where also not converted, so we have to do this
                            # manually, too.
                            pd.to_datetime(v, utc=True) if n in [0, 1] else v
                            for k, v in sorted(
                                s[n].items(), key=lambda kv: int(kv[0])
                            )
                        ]
                        for n in s.index
                    ]
                )
            )
        )
        return cls.from_df(df)

    def df(self, location=None, lib=None):
        if lib is None and location is None:
            columns = sorted(set((n, h) for (xy, n, h) in self.series))
            index = sorted(xy for xy in set(xy for (xy, n, h) in self.series))
            data = {
                (n, h): [self.series[xy, n, h] for xy in index]
                for (n, h) in columns
            }
            return DF(index=pd.MultiIndex.from_tuples(index), data=data)

        if lib is None:
            raise NotImplementedError(
                "Arbitrary dataframes not supported yet.\n"
                'Please use one of `lib="pvlib"` or `lib="windpowerlib"`.'
            )

        xy = (location.x, location.y)
        location = (
            self.locations[xy]
            if xy in self.locations
            else to_shape(self.location(location).point)
            if self.session is not None
            else min(
                self.locations.values(),
                key=lambda point: location.distance(point),
            )
        )
        point = (location.x, location.y)

        index = (
            [
                dhi[0] + (dhi[1] - dhi[0]) / 2
                for dhi in self.series[point, "ASWDIFD_S", 0]
            ]
            if lib == "pvlib"
            else [
                wind_speed[0]
                for wind_speed in self.series[
                    point, "VABS_AV", self.variables["VABS_AV"]["heights"][0]
                ]
            ]
            if lib == "windpowerlib"
            else []
        )

        def to_series(v, h):
            s = self.series[point, v, h]
            return Series([p[2] for p in s], index=[p[0] for p in s])

        series = {
            (k[0] if lib == "pvlib" else k): sum(
                to_series(*p, *k[1:]) for p in TRANSLATIONS[lib][k[0]]
            )
            for k in (
                [
                    ("dhi",),
                    ("dni",),
                    ("ghi",),
                    ("pressure",),
                    ("temp_air",),
                    ("wind_speed",),
                ]
                if lib == "pvlib"
                else [
                    (v, h)
                    for v in [
                        "pressure",
                        "roughness_length",
                        "temperature",
                        "wind_speed",
                    ]
                    for h in self.variables[TRANSLATIONS[lib][v][0][0]][
                        "heights"
                    ]
                ]
                if lib == "windpowerlib"
                else [(v,) for v in self.variables]
            )
        }
        if lib == "pvlib":
            series["temp_air"] = (
                (series["temp_air"] - 273.15)
                .resample("15min")
                .interpolate()[series["dhi"].index]
            )
            series["pressure"] = (
                series["pressure"]
                .resample("15min")
                .interpolate()[series["dhi"].index]
            )
            ws = series["wind_speed"]
            for k in series["wind_speed"].keys():
                ws[k + TD("15min")] = ws[k]
            ws.sort_index(inplace=True)
        if lib == "windpowerlib":
            roughness = TRANSLATIONS[lib]["roughness_length"][0][0]
            series.update(
                {
                    ("roughness_length", h): series["roughness_length", h]
                    .resample("30min")
                    .interpolate()[index]
                    for h in self.variables[roughness]["heights"]
                }
            )
            series.update({k: series[k][index] for k in series})
        return DF(index=index, data={k: series[k].values for k in series})
