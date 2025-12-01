# -*- coding: utf-8 -*
"""
Feed-in model class using pvlib.

SPDX-FileCopyrightText: Birgit Schachler
SPDX-FileCopyrightText: Uwe Krien <krien@uni-bremen.de>
SPDX-FileCopyrightText: Stephan Günther
SPDX-FileCopyrightText: Stephen Bosch
SPDX-FileCopyrightText: Patrik Schönfeldt <patrik.schoenfeldt@dlr.de>

SPDX-License-Identifier: MIT

This module holds an implementations of a photovoltaic feed-in model
using the python library pvlib.
"""

from pvlib.location import Location as PvlibLocation
from pvlib.modelchain import ModelChain as PvlibModelChain
from pvlib.pvsystem import PVSystem as PvlibPVSystem

from .base import PhotovoltaicModelBase
from .base import get_power_plant_data


class Pvlib(PhotovoltaicModelBase):
    r"""
    Model to determine the feed-in of a photovoltaic module using the pvlib.

    The pvlib [1]_ is a python library for simulating the performance of
    photovoltaic energy systems. For more information about the photovoltaic
    model check the documentation of the pvlib [2]_.

    Notes
    ------
    In order to use this model various power plant and model parameters have to
    be provided. See :attr:`~.power_plant_requires` as well as
    :attr:`~.requires` for further information. Furthermore, the weather
    data used to calculate the feed-in has to have a certain format. See
    :meth:`~.feedin` for further information.

    References
    ----------
    .. [1] `pvlib on github <https://github.com/pvlib/pvlib-python>`_
    .. [2] `pvlib documentation <https://pvlib-python.readthedocs.io>`_

    See Also
    --------
    :class:`~.models.Base`
    :class:`~.models.PhotovoltaicModelBase`

    """

    def __init__(self, **kwargs):
        """
        """
        super().__init__(**kwargs)
        self.power_plant = None

    def __repr__(self):
        return "pvlib"

    @property
    def power_plant_requires(self):
        r"""
        The power plant parameters this model requires to calculate a feed-in.

        The required power plant parameters are:

        `module_name`, `inverter_name`, `azimuth`, `tilt`,
        `albedo/surface_type`

        module_name (str)
            Name of the PV module as in the Sandia module database. Use
            :func:`~.get_power_plant_data` with `dataset` = 'sandiamod' to get
            an overview of all provided modules. See the data set documentation
            [3]_ for further information on provided parameters.
        inverter_name (str)
            Name of the inverter as in the CEC inverter database. Use
            :func:`~.get_power_plant_data` with `dataset` = 'cecinverter' to
            get an overview of all provided inverters. See the data set
            documentation [4]_ for further information on provided parameters.
        azimuth (float)
            Azimuth angle of the module surface (South=180).

            See also :pvlib:`PVSystem.surface_azimuth <pvlib.pvsystem.\
            PVSystem.surface_azimuth>` in pvlib documentation.
        tilt (float)
            Surface tilt angle in decimal degrees.
            The tilt angle is defined as degrees from horizontal
            (e.g. surface facing up = 0, surface facing horizon = 90).

            See also :pvlib:`PVSystem.surface_tilt <pvlib.pvsystem.PVSystem.\
            surface_tilt>` in pvlib documentation.
        albedo (float)
            The ground albedo. See also :pvlib:`PVSystem.albedo <pvlib.\
            pvsystem.PVSystem.albedo>` in pvlib documentation.
        surface_type (str)
            The ground surface type. See `SURFACE_ALBEDOS` in
            `pvlib.irradiance <https://github.com/pvlib/pvlib-python/blob/master/pvlib/irradiance.py>`_ module for valid values.

        References
        ----------
        .. [3] `Sandia module database documentation <https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi/2004/043535.pdf>`_
        .. [4] `CEC inverter database documentation <https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi/2007/075036.pdf>`_

        """  # noqa: E501
        # ToDo Maybe add method to assign suitable inverter if none is
        # specified
        required = [
            "azimuth",
            "tilt",
            "module_name",
            ["albedo", "surface_type"],
            "inverter_name",
            "module_type",
            "racking_model"
        ]
        # ToDo @Günni: is this necessary?
        if super().power_plant_requires is not None:
            required.extend(super().power_plant_requires)
        return required

    @property
    def requires(self):
        r"""
        The parameters this model requires to calculate a feed-in.

        The required model parameters are:

        `location`

        location (:obj:`tuple` or :shapely:`Point`)
            Geo location of the PV system. Can either be provided as a tuple
            with first entry being the latitude and second entry being the
            longitude or as a :shapely:`Point`.

        """
        required = ["location"]
        if super().requires is not None:
            required.extend(super().requires)
        return required

    @property
    def pv_system_area(self):
        """
        Area of PV system in :math:`m^2`.

        """
        if self.power_plant:
            return (
                self.power_plant.arrays[0].module_parameters.Area
                * self.power_plant.arrays[0].strings
                * self.power_plant.arrays[0].modules_per_string
            )
        else:
            return None

    @property
    def pv_system_peak_power(self):
        """
        Peak power of PV system in Watt.

        The peak power of the PV system can either be limited by the inverter
        or the PV module(s), wherefore in the case the `mode` parameter,
        which specifies whether AC or DC feed-in is calculated, is set to
        'ac' (which is the default), the minimum of AC inverter power and
        maximum power of the module(s) is returned. In the case that
        `mode` is set to 'dc' the inverter power is not considered and the
        peak power is equal to the maximum power of the module(s).

        """
        if self.power_plant:
            if self.mode == "ac":
                return min(
                    self.power_plant.arrays[0].module_parameters.Impo
                    * self.power_plant.arrays[0].module_parameters.Vmpo
                    * self.power_plant.arrays[0].strings
                    * self.power_plant.arrays[0].modules_per_string,
                    self.power_plant.inverter_parameters.Paco,
                )
            elif self.mode == "dc":
                return (
                    self.power_plant.arrays[0].module_parameters.Impo
                    * self.power_plant.arrays[0].module_parameters.Vmpo
                    * self.power_plant.arrays[0].strings
                    * self.power_plant.arrays[0].modules_per_string
                )
            else:
                raise ValueError(
                    "{} is not a valid `mode`. `mode` must "
                    "either be 'ac' or 'dc'.".format(self.mode)
                )
        else:
            return None

    def _power_plant_requires_check(self, parameters):
        """
        Function to check if all required power plant parameters are provided.

        Power plant parameters this model requires are specified in
        :attr:`~.models.Pvlib.power_plant_requires`.

        Parameters
        -----------
        parameters : list(str)
            List of provided power plant parameters.

        """
        for k in self.power_plant_requires:
            if not isinstance(k, list):
                if k not in parameters:
                    raise AttributeError(
                        "The specified model '{model}' requires power plant "
                        "parameter '{k}' but it's not provided as an "
                        "argument.".format(k=k, model=self)
                    )
            else:
                # in case one of several parameters can be provided
                if not list(filter(lambda x: x in parameters, k)):
                    raise AttributeError(
                        "The specified model '{model}' requires one of the "
                        "following power plant parameters '{k}' but neither "
                        "is provided as an argument.".format(k=k, model=self)
                    )

    def instantiate_module(self, **kwargs):
        """
        Instantiates a :pvlib:`pvlib.PVSystem <pvlib.pvsystem.PVSystem>`
        object.

        Parameters
        -----------
        **kwargs
            See `power_plant_parameters` parameter in :meth:`~.feedin` for more
            information.

        Returns
        --------
        :pvlib:`pvlib.PVSystem <pvlib.pvsystem.PVSystem>`
            PV system to calculate feed-in for.

        """
        # match all power plant parameters from power_plant_requires property
        # to pvlib's PVSystem parameters
        rename = {
            "module_parameters": get_power_plant_data("SandiaMod")[
                kwargs.pop("module_name")
            ],
            "inverter_parameters": get_power_plant_data("CECInverter")[
                kwargs.pop("inverter_name")
            ],
            "surface_azimuth": kwargs.pop("azimuth"),
            "surface_tilt": kwargs.pop("tilt"),
        }
        # update kwargs with renamed power plant parameters
        kwargs.update(rename)
        return PvlibPVSystem(**kwargs)

    def feedin(self, weather, power_plant_parameters, **kwargs):
        r"""
        Calculates power plant feed-in in Watt.

        This function uses the :pvlib:`pvlib.ModelChain <pvlib.modelchain.\
        ModelChain>` to calculate the feed-in for the given weather time series
        and PV system.
        By default the AC feed-in is returned. Set `mode` parameter to 'dc'
        to retrieve DC feed-in.

        Parameters
        ----------
        weather : :pandas:`pandas.DataFrame<dataframe>`
            Weather time series used to calculate feed-in. See `weather`
            parameter in pvlib's Modelchain :pvlib:`run_model <pvlib.\
            modelchain.ModelChain.run_model>` method for more information on
            required variables, units, etc.
        power_plant_parameters : dict
            Dictionary with power plant specifications. Keys of the dictionary
            are the power plant parameter names, values of the dictionary hold
            the corresponding value. The dictionary must at least contain the
            required power plant parameters (see
            :attr:`~.power_plant_requires`) and may further contain optional
            power plant parameters (see :pvlib:`pvlib.PVSystem <pvlib.\
            pvsystem.PVSystem>`).
        location : :obj:`tuple` or :shapely:`Point`
            Geo location of the PV system. Can either be provided as a tuple
            with first entry being the latitude and second entry being the
            longitude or as a :shapely:`Point`.
        mode : str (optional)
            Can be used to specify whether AC or DC feed-in is returned. By
            default `mode` is 'ac'. To retrieve DC feed-in set `mode` to 'dc'.

            `mode` also influences the peak power of the PV system. See
            :attr:`~.pv_system_peak_power` for more information.
        **kwargs :
            Further keyword arguments can be used to overwrite :pvlib:`pvlib.\
            ModelChain <pvlib.modelchain.ModelChain>` parameters.

        Returns
        -------
        :pandas:`pandas.Series<series>`
            Power plant feed-in time series in Watt.

        """
        self.mode = kwargs.pop("mode", "ac").lower()

        # ToDo Allow usage of feedinlib weather object which makes location
        # parameter obsolete
        location = kwargs.pop("location")
        # ToDo Allow location provided as shapely Point
        location = PvlibLocation(
            latitude=location[0], longitude=location[1], tz=weather.index.tz
        )
        self.power_plant = self.instantiate_module(**power_plant_parameters)

        mc = PvlibModelChain(self.power_plant, location, **kwargs)
        mc.complete_irradiance(weather=weather)
        mc.run_model(weather=weather)

        if self.mode == "ac":
            return mc.results.ac
        elif self.mode == "dc":
            return mc.results.dc.p_mp
        else:
            raise ValueError(
                "{} is not a valid `mode`. `mode` must "
                "either be 'ac' or 'dc'.".format(self.mode)
            )
