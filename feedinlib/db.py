from itertools import chain
from pandas import to_datetime as tdt
from geoalchemy2.elements import WKTElement as WKTE
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sqla
import oedialect

import openFRED as ofr


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
    """ Load weather measurements from an openFRED conforming database.

    Note that you need a database storing weather data using the openFRED
    schema in order to use this class. There is one publicly available at

        https://openenergy-platform.org

    In order to access it, you need the `oedialect` Python package and the, as
    of yet unreleased, `openFRED` package. The former has some important up to
    date fixes which didn't make it into a release yet while the latter isn't
    even properly packaged yet. This means that you have to install both
    packages from source. For the `oedialect` that means you have to do

    ```
    git clone https://github.com/OpenEnergyPlatform/oedialect DIALECTSOURCE
    cd DIALECTSOURCE
    pip install .
    ```

    For `openFRED` you can simply download the `openFRED.py` file from

        https://raw.githubusercontent.com/open-fred/cli/master/openFRED.py

    and put in the directory from which you'll run your scripts. Then the file
    is importable and things should work fine.


    Once you did this, you can simply instantiate a `Weather` object via e.g.:

    ```
    from shapely.geometry import Point

    point = Point(9.7311, 53.3899)
    weather = Weather('2002-01-01', '2002-12-31', [point], ["T"], **defaultdb())
    ```


    Parameters
    ----------
    start : Anything `pandas.to_datetime` can convert to a timestamp
        Load weather data starting from this date.
    stop : Anything `pandas.to_datetime` can convert to a timestamp
        Don't load weather data before this date.
    locations : list of `shapely.geometry.Point`s
        Weather measurements are collected from measurement locations closest
        to the the given points.
    heights : list of numbers
        Limit selected timeseries to these heights. If a variable isn't height
        dependent, i.e. it has only one height, namely `0`, this series is
        selected. Don't select the correspoding variable, in order to avoid
        this.
    variables : list of str or one of "all", "pvlib" or "windpowerlib"
        Load the weather variables specified in the given list, or the
        variables necessary to calculate a feedin using `"pvlib"` or
        `"windpowerlib"` or load` `"all"` variables in the database.
        Defaults to `"all"`.
    regions : list of `shapely.geometry.Polygon`s
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
        heights,
        variables="all",
        regions=None,
        session=None,
        db=None,
    ):
        self.session = session
        self.db = db
        self.locations = (
            {WKTE(l, srid=4326): self.location(l) for l in locations}
            if locations is not None
            else {}
        )
        self.regions = (
            {
                WKTE(r, srid=4326): [l.point for l in self.within(r)]
                for r in regions
            }
            if regions is not None
            else {}
        )
        self.variables = (
            {
                "windpowerlib": ["P", "T", "VABS_AV", "Z0"],
                "pvlib": [
                    "ASWDIFD_S",
                    "ASWDIRN_S",
                    "ASWDIR_S",
                    "T",
                    "VABS_AV",
                ],
                "all": sorted(
                    v.name for v in session.query(db["Variable"]).all()
                ),
            }[variables]
            if variables in ["all", "pvlib", "windpowerlib"]
            else variables
        )

        self.series = {
            (v, h, l): sorted(
                (
                    (segment_start, segment_stop, value)
                    for series in chain(
                        q.filter(
                            (db["Timespan"].stop >= tdt(start))
                            & (db["Timespan"].start <= tdt(stop))
                        )
                        .distinct()
                        .all()
                    )
                    for (segment, value) in zip(
                        series.timespan.segments, series.values
                    )
                    for segment_start in [tdt(segment[0])]
                    for segment_stop in [tdt(segment[1])]
                    if segment_start >= tdt(start)
                    and segment_stop <= tdt(stop)
                ),
                key=lambda s: s[0],
            )
            for v in self.variables
            for l in chain(self.locations.values(), *self.regions.values())
            for variable_heights in (
                set(
                    h[0]
                    for h in session.query(db["Series"].height)
                    .join(db["Variable"])
                    .filter(db["Variable"].name == v)
                    .distinct()
                    .all()
                ),
            )
            for h in (
                {0}
                if variable_heights == {0.0}
                else variable_heights.intersection(heights)
            )
            for q in [
                session.query(db["Series"])
                .filter(
                    (db["Series"].height == h) & (db["Series"].location == l)
                )
                .join(db["Variable"])
                .filter(db["Variable"].name == v)
                .join(db["Timespan"])
            ]
        }

    def location(self, point=None):
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
        region = WKTE(regions.to_wkt(), srid=4326)
        return (
            self.session.query(self.db["Location"])
            .filter(self.db["Location"].point.ST_Within(region))
            .all()
        )

    def __call__(start=None, stop=None, locations=None):
        pass
