""" Your one stop shop for generating (renewable energy) feedin time series.
"""

class Feedin:
    """ Generates a feedin timeseries when called.

    Feedins are callable objects, generating a feedin timeseries when
    called. The parameters necessary to determine the feedin may be
    stored as attributes of the feedin object or they may be temporarily
    overridden by supplying them as arguments to a specific call.
    Additionally, one can generate multiple feedin timeseries for
    different parameter variations by supplying multiple values for a
    parameter, like e.g. multiple locations and/or weather objects.


    Attributes
    ----------


    Parameters
    ----------

    weather
        A weather object.

    model
        Model used to calculate the feedin time series. It is here where
        you differentiate e.g. whether you want to calculate the feedin
        time series for a photovoltaic or a wind power plant, by
        specifying a specific photovoltaic or wind power model.
        Obviously this has consequences for which additional parameters
        are needed to calculate a feedin time series.

    """
    # TODO: Figure out a good way to index those feedin time series by
    #       parameter variations.

    def __init__(self, *xs, **ks):
        pass

    def __call__(self, *xs, **ks):
        """ Calculate a feedin time series.

        Calculates a feedin time series based on the parameters stored
        on this object, optionally overridden by the arguments.

        """
        pass

