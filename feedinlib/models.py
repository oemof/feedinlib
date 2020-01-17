# -*- coding: utf-8 -*-

"""
Feed-in model classes.

This module provides abstract classes as blueprints for classes that implement
feed-in models for weather dependent renewable energy resources. These models
take in power plant and weather data to calculate power plant feed-in.
Furthermore, this module holds implementations of feed-in models. So far models
using the python libraries pvlib and windpowerlib to calculate photovoltaic and
wind power feed-in, respectively, have been implemented.

"""

from abc import ABC, abstractmethod
import warnings
import pandas as pd
from copy import deepcopy

from windpowerlib import ModelChain as WindpowerlibModelChain
from windpowerlib import (
    TurbineClusterModelChain as WindpowerlibClusterModelChain,
)
from windpowerlib import WindTurbine as WindpowerlibWindTurbine
from windpowerlib import WindFarm as WindpowerlibWindFarm
from windpowerlib import WindTurbineCluster as WindpowerlibWindTurbineCluster
from windpowerlib import get_turbine_types

from pvlib.modelchain import ModelChain as PvlibModelChain
from pvlib.pvsystem import PVSystem as PvlibPVSystem
from pvlib.location import Location as PvlibLocation
import pvlib.pvsystem

import feedinlib.powerplants


class Base(ABC):
    r"""
    The base class of feedinlib models.

    This base class is an abstract class serving as a blueprint for classes
    that implement feed-in models for weather dependent renewable energy
    resources. It forces implementors to implement certain properties and
    methods.

    """

    def __init__(self, **kwargs):
        """
        """
        self._power_plant_requires = kwargs.get("powerplant_requires", None)
        self._requires = kwargs.get("requires", None)

    @property
    @abstractmethod
    def power_plant_requires(self):
        """
        The (names of the) power plant parameters this model requires in
        order to calculate the feed-in.

        As this is an abstract property you have to override it in a subclass
        so that the model can be instantiated. This forces implementors to make
        the required power plant parameters for a model explicit, even if they
        are empty, and gives them a good place to document them.

        By default, this property is settable and its value can be specified
        via an argument upon construction. If you want to keep this
        functionality, simply delegate all calls to the superclass.

        Parameters
        ----------
        names : list(str), optional
            Containing the names of the required power plant parameters.

        """
        return self._power_plant_requires

    @power_plant_requires.setter
    def power_plant_requires(self, names):
        self._power_plant_requires = names

    def _power_plant_requires_check(self, parameters):
        """
        Function to check if all required power plant parameters are provided.

        This function only needs to be implemented in a subclass in case
        required power plant parameters specified in
        :attr:`power_plant_requires` are not a simple list that can be checked
        by :func:`~.power_plants.Base.check_models_power_plant_requirements`.

        """
        raise NotImplementedError

    @property
    @abstractmethod
    def requires(self):
        """
        The (names of the) parameters this model requires in order to
        calculate the feed-in.

        As this is an abstract property you have to override it in a subclass
        so that the model can be instantiated. This forces implementors to make
        the required model parameters explicit, even if they
        are empty, and gives them a good place to document them.

        By default, this property is settable and its value can be specified
        via an argument upon construction. If you want to keep this
        functionality, simply delegate all calls to the superclass.

        Parameters
        ----------
        names : list(str), optional
            Containing the names of the required power plant parameters.

        """
        return self._requires

    @requires.setter
    def requires(self, names):
        self._requires = names

    @abstractmethod
    def feedin(self, weather, power_plant_parameters, **kwargs):
        """
        Calculates power plant feed-in in Watt.

        As this is an abstract method you have to override it in a subclass
        so that the power plant feed-in using the respective model can be
        calculated.

        Parameters
        ----------
        weather :
            Weather data to calculate feed-in. Format and required parameters
            depend on the model.
        power_plant_parameters : dict
            Dictionary with power plant specifications. Keys of the dictionary
            are the power plant parameter names, values of the dictionary hold
            the corresponding value. The dictionary must at least contain the
            power plant parameters required by the respective model and may
            further contain optional power plant parameters. See
            `power_plant_requires` property of the respective model for futher
            information.
        **kwargs :
            Keyword arguments for respective model's feed-in calculation.

        Returns
        -------
        feedin : :pandas:`pandas.Series<series>`
            Series with power plant feed-in for specified time span in Watt.
            If respective model does calculate AC and DC feed-in, AC feed-in
            should be returned by default. `mode` parameter can be used to
            overwrite this default behavior and return DC power output instead
            (for an example see :meth:`~.models.Pvlib.feedin`).

        """
        pass


class PhotovoltaicModelBase(Base):
    """
    Expands model base class :class:`~.models.Base` by PV specific attributes.

    """

    @property
    @abstractmethod
    def pv_system_area(self):
        r"""
        Area of PV system in :math:`m^2`.

        As this is an abstract property you have to override it in a subclass
        so that the model can be instantiated. This forces implementors to
        provide a way to retrieve the area of the PV system that is e.g. used
        to scale the feed-in by area.

        """

    @property
    @abstractmethod
    def pv_system_peak_power(self):
        """
        Peak power of PV system in Watt.

        As this is an abstract property you have to override it in a subclass
        so that the model can be instantiated. This forces implementors to
        provide a way to retrieve the peak power of the PV system that is e.g.
        used to scale the feed-in by installed capacity.

        """


class WindpowerModelBase(Base):
    """
    Expands model base class :class:`~.models.Base` by wind power specific
    attributes.

    """

    @property
    @abstractmethod
    def nominal_power_wind_power_plant(self):
        """
        Nominal power of wind power plant in Watt.

        As this is an abstract property you have to override it in a subclass
        so that the model can be instantiated. This forces implementors to
        provide a way to retrieve the nominal power of the wind power plant
        that is e.g. used to scale the feed-in by installed capacity.

        """


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

        """
        # ToDo Maybe add method to assign suitable inverter if none is
        # specified
        required = [
            "azimuth",
            "tilt",
            "module_name",
            ["albedo", "surface_type"],
            "inverter_name",
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
                self.power_plant.module_parameters.Area
                * self.power_plant.strings_per_inverter
                * self.power_plant.modules_per_string
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
                    self.power_plant.module_parameters.Impo
                    * self.power_plant.module_parameters.Vmpo
                    * self.power_plant.strings_per_inverter
                    * self.power_plant.modules_per_string,
                    self.power_plant.inverter_parameters.Paco,
                )
            elif self.mode == "dc":
                return (
                    self.power_plant.module_parameters.Impo
                    * self.power_plant.module_parameters.Vmpo
                    * self.power_plant.strings_per_inverter
                    * self.power_plant.modules_per_string
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
            return mc.ac
        elif self.mode == "dc":
            return mc.dc.p_mp
        else:
            raise ValueError(
                "{} is not a valid `mode`. `mode` must "
                "either be 'ac' or 'dc'.".format(self.mode)
            )


class WindpowerlibTurbine(WindpowerModelBase):
    r"""
    Model to determine the feed-in of a wind turbine using the windpowerlib.

    The windpowerlib [1]_ is a python library for simulating the performance of
    wind turbines and farms. For more information about the model check the
    documentation of the windpowerlib [2]_.

    Notes
    ------
    In order to use this model various power plant and model parameters have to
    be provided. See :attr:`~.power_plant_requires` as well as
    :attr:`~.requires` for further information. Furthermore, the weather
    data used to calculate the feed-in has to have a certain format. See
    :meth:`~.feedin` for further information.

    References
    ----------
    .. [1] `windpowerlib on github <https://github.com/wind-python/windpowerlib>`_
    .. [2] `windpowerlib documentation <https://windpowerlib.readthedocs.io>`_

    See Also
    --------
    :class:`~.models.Base`
    :class:`~.models.WindpowerModelBase`

    """

    def __init__(self, **kwargs):
        """
        """
        super().__init__(**kwargs)
        self.power_plant = None

    def __repr__(self):
        return "windpowerlib_single_turbine"

    @property
    def power_plant_requires(self):
        r"""
        The power plant parameters this model requires to calculate a feed-in.

        The required power plant parameters are:

        `hub_height`, `power_curve/power_coefficient_curve/turbine_type`

        hub_height (float)
            Hub height in m.

            See also :wind_turbine:`WindTurbine.hub_height <windpowerlib.\
            wind_turbine.WindTurbine.hub_height>` in windpowerlib
            documentation.
        power_curve (:pandas:`pandas.DataFrame<frame>` or dict)
            DataFrame/dictionary with wind speeds in m/s and corresponding
            power curve value in W.

            See also :wind_turbine:`WindTurbine.power_curve <windpowerlib.\
            wind_turbine.WindTurbine.power_curve>` in windpowerlib
            documentation.
        power_coefficient_curve (:pandas:`pandas.DataFrame<frame>` or dict)
            DataFrame/dictionary with wind speeds in m/s and corresponding
            power coefficient.

            See also :wind_turbine:`WindTurbine.power_coefficient_curve \
            <windpowerlib.wind_turbine.WindTurbine.power_coefficient_curve>`
            in windpowerlib documentation.
        turbine_type (str)
            Name of the wind turbine type as in the oedb turbine library. Use
            :func:`~.get_power_plant_data` with `dataset` =
            'oedb_turbine_library' to get an overview of all provided turbines.
            See the data set metadata [3]_ for further information on provided
            parameters.

        References
        ----------
        .. [3] `oedb wind turbine library <https://openenergy-platform.org/dataedit/view/supply/wind_turbine_library>`_

        """
        required = [
            "hub_height",
            ["power_curve", "power_coefficient_curve", "turbine_type"],
        ]
        if super().power_plant_requires is not None:
            required.extend(super().power_plant_requires)
        return required

    @property
    def requires(self):
        r"""
        The parameters this model requires to calculate a feed-in.

        This model does not require any additional model parameters.

        """
        required = []
        if super().requires is not None:
            required.extend(super().requires)
        return required

    @property
    def nominal_power_wind_power_plant(self):
        """
        Nominal power of wind turbine in Watt.

        See :wind_turbine:`WindTurbine.nominal_power <windpowerlib.\
        wind_turbine.WindTurbine.nominal_power>` in windpowerlib for further
        information.

        """
        if self.power_plant:
            return self.power_plant.nominal_power
        else:
            return None

    def _power_plant_requires_check(self, parameters):
        """
        Function to check if all required power plant parameters are provided.

        Power plant parameters this model requires are specified in
        :attr:`~.power_plant_requires`.

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

    def instantiate_turbine(self, **kwargs):
        """
        Instantiates a :windpowerlib:`windpowerlib.WindTurbine \
        <windpowerlib.wind_turbine.WindTurbine>` object.

        Parameters
        -----------
        **kwargs
            See `power_plant_parameters` parameter in :meth:`~.feedin` for more
            information.

        Returns
        --------
        :windpowerlib:`windpowerlib.WindTurbine \
            <windpowerlib.wind_turbine.WindTurbine>`
            Wind turbine to calculate feed-in for.

        """
        return WindpowerlibWindTurbine(**kwargs)

    def feedin(self, weather, power_plant_parameters, **kwargs):
        r"""
        Calculates power plant feed-in in Watt.

        This function uses the windpowerlib's :windpowerlib:`ModelChain \
        <windpowerlib.modelchain.ModelChain>` to calculate the feed-in for the
        given weather time series and wind turbine.

        Parameters
        ----------
        weather : :pandas:`pandas.DataFrame<dataframe>`
            Weather time series used to calculate feed-in. See `weather_df`
            parameter in windpowerlib's Modelchain :windpowerlib:`run_model \
            <windpowerlib.modelchain.ModelChain.run_model>` method for
            more information on required variables, units, etc.
        power_plant_parameters : dict
            Dictionary with power plant specifications. Keys of the dictionary
            are the power plant parameter names, values of the dictionary hold
            the corresponding value. The dictionary must at least contain the
            required power plant parameters (see
            :attr:`~.power_plant_requires`) and may further contain optional
            power plant parameters (see :windpowerlib:`windpowerlib.\
            WindTurbine <windpowerlib.wind_turbine.WindTurbine>`).
        **kwargs :
            Keyword arguments can be used to overwrite the windpowerlib's
            :windpowerlib:`ModelChain <windpowerlib.modelchain.ModelChain>`
            parameters.

        Returns
        -------
        :pandas:`pandas.Series<series>`
            Power plant feed-in time series in Watt.

        """
        self.power_plant = self.instantiate_turbine(**power_plant_parameters)
        mc = WindpowerlibModelChain(self.power_plant, **kwargs)
        return mc.run_model(weather).power_output


class WindpowerlibTurbineCluster(WindpowerModelBase):
    """
    Model to determine the feed-in of a wind turbine cluster using the
    windpowerlib.

    The windpowerlib [1]_ is a python library for simulating the performance of
    wind turbines and farms. For more information about the model check the
    documentation of the windpowerlib [2]_.

    Notes
    ------
    In order to use this model various power plant and model parameters have to
    be provided. See :attr:`~.power_plant_requires` as well as
    :attr:`~.requires` for further information. Furthermore, the weather
    data used to calculate the feed-in has to have a certain format. See
    :meth:`~.feedin` for further information.

    See Also
    --------
    :class:`~.models.Base`
    :class:`~.models.WindpowerModelBase`

    References
    ----------
    .. [1] `windpowerlib on github <https://github.com/wind-python/windpowerlib>`_
    .. [2] `windpowerlib documentation <https://windpowerlib.readthedocs.io>`_

    """

    def __init__(self, **kwargs):
        """
        """
        super().__init__(**kwargs)
        self.power_plant = None

    def __repr__(self):
        return "WindpowerlibTurbineCluster"

    @property
    def power_plant_requires(self):
        r"""
        The power plant parameters this model requires to calculate a feed-in.

        The required power plant parameters are:

        `wind_turbine_fleet/wind_farms`

        The windpowerlib differentiates between wind farms as a group of wind
        turbines (of the same or different type) in the same location and
        wind turbine clusters as wind farms and turbines that are assigned the
        same weather data point to obtain weather data for feed-in calculations
        and can therefore be clustered to speed up calculations.
        The `WindpowerlibTurbineCluster` class can be used for both
        :windpowerlib:`windpowerlib.WindFarm <windpowerlib.wind_farm.\
        WindFarm>` and :windpowerlib:`windpowerlib.WindTurbineCluster \
        <windpowerlib.wind_turbine_cluster.WindTurbineCluster>` calculations.
        To set up a :windpowerlib:`windpowerlib.WindFarm <windpowerlib.\
        wind_farm.WindFarm>` please provide a `wind_turbine_fleet`
        and to set up a :windpowerlib:`windpowerlib.WindTurbineCluster \
        <windpowerlib.wind_turbine_cluster.WindTurbineCluster>` please
        provide a list of `wind_farms`. See below for further information.

        wind_turbine_fleet (:pandas:`pandas.DataFrame<frame>`)
            The wind turbine fleet specifies the turbine types and their
            corresponding number or total installed capacity in the wind farm.
            DataFrame must have columns 'wind_turbine' and either
            'number_of_turbines' (number of wind turbines of the same turbine
            type in the wind farm, can be a float) or 'total_capacity'
            (installed capacity of wind turbines of the same turbine type in
            the wind farm in Watt).

            The wind turbine in column 'wind_turbine' can be provided as a
            :class:`~.powerplants.WindPowerPlant` object, a dictionary with
            power plant parameters (see
            :attr:`~.models.WindpowerlibTurbine.power_plant_requires`
            for required parameters) or a :windpowerlib:`windpowerlib.\
            WindTurbine <windpowerlib.wind_turbine.WindTurbine>`.

            See also `wind_turbine_fleet` parameter of
            :windpowerlib:`windpowerlib.WindFarm <windpowerlib.wind_farm.\
            WindFarm>`.

            The wind turbine fleet may also be provided as a list of
            :windpowerlib:`windpowerlib.WindTurbineGroup <windpowerlib.\
            wind_turbine.WindTurbineGroup>` as described there.
        wind_farms (list(dict) or list(:windpowerlib:`windpowerlib.WindFarm <windpowerlib.wind_farm.WindFarm>`))
            List of wind farms in cluster. Wind farms in the list can either
            be provided as :windpowerlib:`windpowerlib.WindFarm \
            <windpowerlib.wind_farm.WindFarm>` or as dictionaries
            where the keys of the dictionary are the wind farm parameter names
            and the values of the dictionary hold the corresponding value.
            The dictionary must at least contain a wind turbine fleet (see
            'wind_turbine_fleet' parameter specifications above) and may
            further contain optional wind farm parameters (see
            :windpowerlib:`windpowerlib.WindFarm <windpowerlib.wind_farm.\
            WindFarm>`).

        """
        required = ["wind_turbine_fleet", "wind_farms"]
        if super().power_plant_requires is not None:
            required.extend(super().power_plant_requires)
        return required

    @property
    def requires(self):
        r"""
        The parameters this model requires to calculate a feed-in.

        This model does not require any additional model parameters.

        """
        required = []
        if super().requires is not None:
            required.extend(super().requires)
        return required

    @property
    def nominal_power_wind_power_plant(self):
        """
        Nominal power of wind turbine cluster in Watt.

        The nominal power is the sum of the nominal power of all turbines.
        See `nominal_power` of :windpowerlib:`windpowerlib.WindFarm \
        <windpowerlib.wind_farm.WindFarm>` or
        :windpowerlib:`windpowerlib.WindTurbineCluster \
        <windpowerlib.wind_turbine_cluster.WindTurbineCluster>` for further
        information.

        """
        if self.power_plant:
            return self.power_plant.nominal_power
        else:
            return None

    def _power_plant_requires_check(self, parameters):
        r"""
        Function to check if all required power plant parameters are provided.

        Power plant parameters this model requires are specified in
        :attr:`~.power_plant_requires`.

        Parameters
        -----------
        parameters : list(str)
            List of provided power plant parameters.

        """
        if not any([_ in parameters for _ in self.power_plant_requires]):
            raise KeyError(
                "The specified model '{model}' requires one of the following "
                "power plant parameters: {parameters}".format(
                    model=self, parameters=self.power_plant_requires
                )
            )

    def instantiate_turbine(self, **kwargs):
        """
        Instantiates a :windpowerlib:`windpowerlib.WindTurbine \
        <windpowerlib.wind_turbine.WindTurbine>` object.

        Parameters
        -----------
        **kwargs
            Dictionary with wind turbine specifications. Keys of the dictionary
            are the power plant parameter names, values of the dictionary hold
            the corresponding value. The dictionary must at least contain the
            required turbine parameters (see
            :attr:`~.models.WindpowerlibTurbine.power_plant_requires`) and
            may further contain optional power plant parameters (see
            :windpowerlib:`windpowerlib.WindTurbine \
            <windpowerlib.wind_turbine.WindTurbine>`).

        Returns
        --------
        :windpowerlib:`windpowerlib.WindTurbine \
        <windpowerlib.wind_turbine.WindTurbine>`
            Wind turbine in wind farm or turbine cluster.

        """
        power_plant = WindpowerlibWindTurbine(**kwargs)
        return power_plant

    def instantiate_windfarm(self, **kwargs):
        r"""
        Instantiates a :windpowerlib:`windpowerlib.WindFarm <windpowerlib.\
        wind_farm.WindFarm>` object.

        Parameters
        ----------
        **kwargs
            Dictionary with wind farm specifications. Keys of the dictionary
            are the parameter names, values of the dictionary hold the
            corresponding value. The dictionary must at least contain a wind
            turbine fleet (see 'wind_turbine_fleet' specifications in
            :attr:`~.power_plant_requires`) and may further contain optional
            wind farm parameters (see :windpowerlib:`windpowerlib.WindFarm \
            <windpowerlib.wind_farm.WindFarm>`).

        Returns
        --------
        :windpowerlib:`windpowerlib.WindFarm <windpowerlib.wind_farm.WindFarm>`

        """
        # deepcopy turbine fleet to not alter original turbine fleet
        wind_turbine_fleet = deepcopy(kwargs.pop("wind_turbine_fleet"))

        # if turbine fleet is provided as list, it is assumed that list
        # contains WindTurbineGroups and WindFarm can be directly instantiated
        if isinstance(wind_turbine_fleet, list):
            return WindpowerlibWindFarm(wind_turbine_fleet, **kwargs)

        # if turbine fleet is provided as DataFrame wind turbines in
        # 'wind_turbine' column have to be converted to windpowerlib
        # WindTurbine object
        elif isinstance(wind_turbine_fleet, pd.DataFrame):
            for ix, row in wind_turbine_fleet.iterrows():
                turbine = row["wind_turbine"]
                if not isinstance(turbine, WindpowerlibWindTurbine):
                    if isinstance(
                        turbine, feedinlib.powerplants.WindPowerPlant
                    ):
                        turbine_data = turbine.parameters
                    elif isinstance(turbine, dict):
                        turbine_data = turbine
                    else:
                        raise TypeError(
                            "The WindpowerlibTurbineCluster model requires "
                            "that wind turbines must either be provided as "
                            "WindPowerPlant objects, windpowerlib.WindTurbine "
                            "objects or as dictionary containing all turbine "
                            "parameters required by the WindpowerlibTurbine "
                            "model but type of `wind_turbine` "
                            "is {}.".format(type(row["wind_turbine"]))
                        )
                    # initialize WindpowerlibTurbine instead of directly
                    # initializing windpowerlib.WindTurbine to check required
                    # power plant parameters
                    wind_turbine = WindpowerlibTurbine()
                    wind_turbine._power_plant_requires_check(
                        turbine_data.keys()
                    )
                    wind_turbine_fleet.loc[
                        ix, "wind_turbine"
                    ] = wind_turbine.instantiate_turbine(**turbine_data)
            kwargs["wind_turbine_fleet"] = wind_turbine_fleet
            return WindpowerlibWindFarm(**kwargs)
        else:
            raise TypeError(
                "The WindpowerlibTurbineCluster model requires that the "
                "`wind_turbine_fleet` parameter is provided as a list or "
                "pandas.DataFrame but type of `wind_turbine_fleet` is "
                "{}.".format(type(wind_turbine_fleet))
            )

    def instantiate_turbine_cluster(self, **kwargs):
        r"""
        Instantiates a :windpowerlib:`windpowerlib.WindTurbineCluster \
        <windpowerlib.wind_turbine_cluster.WindTurbineCluster>` object.

        Parameters
        ----------
        **kwargs
            Dictionary with turbine cluster specifications. Keys of the
            dictionary are the parameter names, values of the dictionary hold
            the corresponding value. The dictionary must at least contain a
            list of wind farms (see 'wind_farms' specifications in
            :attr:`~.power_plant_requires`) and may further contain optional
            wind turbine cluster parameters (see
            :windpowerlib:`windpowerlib.WindTurbineCluster \
            <windpowerlib.wind_turbine_cluster.WindTurbineCluster>`).

        Returns
        --------
        :windpowerlib:`windpowerlib.WindTurbineCluster <windpowerlib.wind_turbine_cluster.WindTurbineCluster>`

        """
        wind_farm_list = []
        for wind_farm in kwargs.pop("wind_farms"):
            if not isinstance(wind_farm, WindpowerlibWindFarm):
                wind_farm_list.append(self.instantiate_windfarm(**wind_farm))
            else:
                wind_farm_list.append(wind_farm)
        kwargs["wind_farms"] = wind_farm_list
        return WindpowerlibWindTurbineCluster(**kwargs)

    def feedin(self, weather, power_plant_parameters, **kwargs):
        r"""
        Calculates power plant feed-in in Watt.

        This function uses the windpowerlib's
        :windpowerlib:`TurbineClusterModelChain <windpowerlib.\
        turbine_cluster_modelchain.TurbineClusterModelChain>` to calculate the
        feed-in for the given weather time series and wind farm or cluster.

        Parameters
        ----------
        weather : :pandas:`pandas.DataFrame<dataframe>`
            Weather time series used to calculate feed-in. See `weather_df`
            parameter in windpowerlib's TurbineClusterModelChain
            :windpowerlib:`run_model <windpowerlib.turbine_cluster_modelchain.\
            TurbineClusterModelChain.run_model>` method for more information on
            required variables, units, etc.
        power_plant_parameters : dict
            Dictionary with either wind farm or wind turbine cluster
            specifications. For more information on wind farm parameters see
            `kwargs` in :meth:`~.instantiate_windfarm`.
            For information on turbine cluster parameters see `kwargs`
            in :meth:`~.instantiate_turbine_cluster`.
        **kwargs :
            Keyword arguments can be used to overwrite the windpowerlib's
            :windpowerlib:`TurbineClusterModelChain <windpowerlib.\
            turbine_cluster_modelchain.TurbineClusterModelChain>` parameters.

        Returns
        -------
        :pandas:`pandas.Series<series>`
            Power plant feed-in time series in Watt.

        """
        # wind farm calculation
        if "wind_turbine_fleet" in power_plant_parameters.keys():
            self.power_plant = self.instantiate_windfarm(
                **power_plant_parameters
            )
        # wind cluster calculation
        else:
            self.power_plant = self.instantiate_turbine_cluster(
                **power_plant_parameters
            )
        mc = WindpowerlibClusterModelChain(self.power_plant, **kwargs)
        return mc.run_model(weather).power_output


def get_power_plant_data(dataset, **kwargs):
    r"""
    Function to retrieve power plant data sets provided by feed-in models.

    This function can be used to retrieve power plant data from data sets
    and to get an overview of which modules, inverters and turbine types are
    provided and can be used in feed-in calculations.

    Parameters
    ----------
    dataset : str
        Specifies data set to retrieve. Possible options are:

        * pvlib PV module and inverter datasets: 'sandiamod', 'cecinverter'

          The original data sets are hosted here:
          https://github.com/NREL/SAM/tree/develop/deploy/libraries

          See :pvlib:`retrieve_sam <pvlib.pvsystem.retrieve_sam>` for further
          information.
        * windpowerlib wind turbine dataset: 'oedb_turbine_library'

          See :windpowerlib:`get_turbine_types <windpowerlib.wind_turbine.\
          get_turbine_types>` for further information.

    **kwargs
        See referenced functions for each dataset above for further optional
        parameters.

    Example
    -------
    >>> from feedinlib import get_power_plant_data
    >>> data = get_power_plant_data('sandiamod')
    >>> # list of all provided PV modules
    >>> pv_modules = data.columns
    >>> print(data.loc["Area", data.columns.str.contains('Aleo_S03')])
    Aleo_S03_160__2007__E__    1.28
    Aleo_S03_165__2007__E__    1.28
    Name: Area, dtype: object

    """
    dataset = dataset.lower()
    if dataset in ["sandiamod", "cecinverter"]:
        return pvlib.pvsystem.retrieve_sam(
            name=dataset, path=kwargs.get("path", None)
        )
    elif dataset == "oedb_turbine_library":
        return get_turbine_types(
            turbine_library=kwargs.get("turbine_library", "local"),
            print_out=kwargs.get("print_out", False),
            filter_=kwargs.get("filter_", True),
        )
    else:
        warnings.warn("Unknown dataset {}.".format(dataset))
        return None
