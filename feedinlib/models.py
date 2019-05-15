# -*- coding: utf-8 -*-
"""
@author: oemof developer group
"""

from abc import ABC, abstractmethod

# windpowerlib
from windpowerlib import ModelChain as WindpowerlibModelChain
from windpowerlib import TurbineClusterModelChain \
    as WindpowerlibClusterModelChain
from windpowerlib import WindTurbine as WindpowerlibWindTurbine
from windpowerlib import WindFarm as WindpowerlibWindFarm
from windpowerlib import WindTurbineCluster as WindpowerlibWindTurbineCluster

# pvlib
from pvlib.modelchain import ModelChain as PvlibModelChain
from pvlib.pvsystem import PVSystem as PvlibPVSystem
from pvlib.location import Location as PvlibLocation
import pvlib.pvsystem

import feedinlib.powerplants


class Base(ABC):
    r""" The base class of feedinlib models.

    As this is an abstract property, you have to override it in a subclass
    so that the model can be instantiated. This forces implementors to make
    the required parameters for a model explicit, even if they are empty,
    and gives them a good place to document them.

    By default, this property is settable and its value can be specified
    via and argument on construction. If you want to keep this
    functionality, simply delegate all calls to the superclass.

    Parameters
    ----------
    required : list of strings, optional
        Containing the names of the required parameters to use the model.

    # ToDo: Docstring
    """
    def __init__(self, **kwargs):
        self._powerplant_requires = None
        self._requires = None

    @property
    @abstractmethod
    def powerplant_requires(self):
        """ The (names of the) power plant parameters this model requires in
        order to calculate the feedin.

        """
        return self._powerplant_requires

    @property
    @abstractmethod
    def requires(self):
        """ The (names of the) parameters this model requires in order to
        calculate the feedin.

        """
        return self._requires


class PhotovoltaicModelBase(Base):
    """
    Expands model base class ModelBase by PV specific attributes

    """
    @property
    @abstractmethod
    def pv_system_area(self):
        """ Area of PV system in m²

        """

    @property
    @abstractmethod
    def pv_system_peak_power(self):
        """ Peak power of PV system in W

        """


class WindpowerModelBase(Base):
    """
    Expands model base class ModelBase by windpower specific attributes

    """
    @property
    @abstractmethod
    def nominal_power_wind_power_plant(self):
        """ Nominal power of turbine or wind park

        """


class Pvlib(PhotovoltaicModelBase):
    r"""Model to determine the output of a photovoltaik module

    The calculation is based on the library pvlib. [1]_

    Parameters
    ----------
    PvlibBased.required (list of strings, optional)
        List of required parameters of the model


    Notes
    -----
    For more information about the photovoltaic model check the documentation
    of the pvlib library.

    https://readthedocs.org/projects/pvlib-python/

    References
    ----------
    .. [1] `pvlib on github <https://github.com/pvlib/pvlib-python>`_

    Examples
    --------
    >>> from feedinlib import models
    >>> pv_model = models.PvlibBased()

    See Also
    --------
    Base
    SimpleWindTurbine
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.powerplant = None

    def __repr__(self):
        return "pvlib"

    @property
    def powerplant_requires(self):
        r""" The parameters this model requires to calculate a feedin.

        In this feedin model the required parameters are:

        :module_name: (string) -
            name of a pv module from the sam.nrel database [12]_
        :tilt: (float) -
            tilt angle of the pv module (horizontal=0°)
        :azimuth: (float) -
            azimuth angle of the pv module (south=180°)
        :albedo: (float) -
            albedo factor arround the module
        """
        # ToDo maybe add method to assign suitable inverter if none is specified
        required = ["azimuth", "tilt", "module_name", "albedo",
                   "inverter_name"]
        if super().powerplant_requires is not None:
            required.extend(super().powerplant_requires)
        return required

    @property
    def requires(self):
        r""" The parameters this model requires to calculate a feedin.

        """
        required = ["location"]
        if super().requires is not None:
            required.extend(super().requires)
        return required

    @property
    def pv_system_area(self):
        if self.powerplant:
            return self.powerplant.module_parameters.Area * \
                   self.powerplant.strings_per_inverter * \
                   self.powerplant.modules_per_string
        else:
            return None

    @property
    def pv_system_peak_power(self):
        if self.powerplant:
            # ToDo Peak power could also be limited by the inverter power!
            return self.powerplant.module_parameters.Impo * \
                   self.powerplant.module_parameters.Vmpo * \
                   self.powerplant.strings_per_inverter * \
                   self.powerplant.modules_per_string
        else:
            return None

    def instantiate_module(self, **kwargs):
        # match all power plant parameters from powerplant_requires property
        # to pvlib's PVSystem parameters
        rename = {
            'module_parameters': self.get_module_data()[
                kwargs.pop('module_name')],
            'inverter_parameters': self.get_converter_data()[
                kwargs.pop('inverter_name')],
            'surface_azimuth': kwargs.pop('azimuth'),
            'surface_tilt': kwargs.pop('tilt'),
            'albedo': kwargs.pop('albedo', None),
            'surface_type': kwargs.pop('surface_type', None)
        }
        # update kwargs with renamed power plant parameters
        kwargs.update(rename)
        self.powerplant = PvlibPVSystem(**kwargs)
        return self.powerplant

    def feedin(self, weather, power_plant_parameters, location, **kwargs):
        r"""
        Feedin time series for the given pv module.

        In contrast to :py:func:`turbine_power_output
        <feedinlib.models.PvlibBased.get_pv_power_output>` it returns just
        the feedin series instead of the whole DataFrame.

        Parameters
        ----------
        see :
            :py:func:`turbine_power_output
            <feedinlib.models.PvlibBased.get_pv_power_output>`

        Returns
        -------
        pandas.Series
            A time series of the power output for the given pv module.
        """
        # The pvlib's ModelChain class with its default settings is used here to
        # calculate the power output. See the documentation of the pvlib if you
        # want to learn more about the ModelChain.
        mc = PvlibModelChain(self.instantiate_module(**power_plant_parameters),
                             PvlibLocation(latitude=location[0], longitude=location[1],
                                           tz=weather.index.tz))
        # Todo Wetterdatenaufbereitung auslagern
        # use the ModelChain's complete_irradiance function to calculate missing dni
        mc.complete_irradiance(times=weather.index, weather=weather)
        mc.run_model()
        return mc.ac

    def get_module_data(self, lib='SandiaMod'):
        r"""
        Fetch the module data from the Sandia Module library

        """
        # ToDo auslagern, sodass nutzer von außen aufrufen können
        return pvlib.pvsystem.retrieve_sam(lib)

    def get_converter_data(self, lib='sandiainverter'):
        r"""
        Fetch the module data from the Sandia Module library

        """
        return pvlib.pvsystem.retrieve_sam(lib)


class WindpowerlibTurbine(WindpowerModelBase):
    r"""Model to determine the output of a wind turbine

    Parameters
    ----------
    required : list of strings
        Containing the names of the required parameters to use the model.

    Examples
    --------
    >>> from feedinlib import models
    >>> required_ls = ['h_hub', 'd_rotor', 'wind_conv_type', 'data_height']
    >>> wind_model = models.SimpleWindTurbine(required=required_ls)

    See Also
    --------
    Base
    PvlibBased
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.powerplant = None

    def __repr__(self):
        return "windpowerlib_single_turbine"

    @property
    def powerplant_requires(self):
        r""" The parameters this model requires to set up a turbine.

        In this feedin model the required parameters are:

        :h_hub: (float) -
            Height of the hub of the wind turbine
        :wind_conv_type: (string) -
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.
        """
        required = ["hub_height", "name", "fetch_curve"]
        if super().powerplant_requires is not None:
            required.extend(super().powerplant_requires)
        return required

    @property
    def requires(self):
        r""" The parameters this model requires to calculate a feedin.

        """
        required = []
        if super().requires is not None:
            required.extend(super().requires)
        return required

    @property
    def nominal_power_wind_power_plant(self):
        if self.powerplant:
            return self.powerplant.nominal_power
        else:
            return None

    def instantiate_turbine(self, **kwargs):
        # match all power plant parameters from powerplant_requires property
        # to windpowerlib's WindTurbine parameters
        rename = {
            'name': kwargs.pop('name'),
            'hub_height': kwargs.pop('hub_height'),
            'fetch_curve': kwargs.pop('fetch_curve')
        }
        # update kwargs with renamed power plant parameters
        kwargs.update(rename)
        self.powerplant = WindpowerlibWindTurbine(**kwargs)
        return self.powerplant

    def feedin(self, weather, power_plant_parameters, **kwargs):
        r"""
        Alias for :py:func:`turbine_power_output
        <feedinlib.models.SimpleWindTurbine.turbine_power_output>`.

        weather : feedinlib Weather Object # @Günni, auch windpowerlibformat erlaubt?
        """
        # ToDo Zeitraum einführen (time_span)
        mc = WindpowerlibModelChain(
            self.instantiate_turbine(**power_plant_parameters), **kwargs)
        return mc.run_model(weather).power_output


class WindpowerlibTurbineCluster(WindpowerModelBase):
    r"""
    Model to determine the output of a wind turbine cluster

    Parameters
    ----------

    Attributes
    ----------

    Examples
    --------

    See Also
    --------
    :class:`~.models.WindpowerModelBase`
    :class:`~.models.Base`

    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.powerplant = None

        # wind farm
        if 'wind_turbine_fleet' in kwargs.keys():
            self.wind_turbine_fleet_init(kwargs['wind_turbine_fleet'])
        # wind turbine cluster
        elif 'wind_farms' in kwargs.keys():
            if isinstance(kwargs['wind_farms'], list):
                for wind_farm in kwargs['wind_farms']:
                    if isinstance(wind_farm, dict) and \
                            'wind_turbine_fleet' in wind_farm.keys():
                        self.wind_turbine_fleet_init(
                            wind_farm['wind_turbine_fleet'])
                    else:
                        raise TypeError(
                            "The WindpowerlibTurbineCluster model requires "
                            "that a wind farm is provided as a dictionary "
                            "with `wind_turbine_fleet` as a key.")
            else:
                raise TypeError(
                    "The WindpowerlibTurbineCluster model requires that "
                    "`wind_farms` parameter is provided as a list but type of"
                    "`wind_farms` is {}.".format(
                        type(kwargs['wind_farms'])))

    def wind_turbine_fleet_init(self, wind_turbine_fleet):
        """
        Sets up a wind turbine fleet list and conducts some type checks

        Parameters
        ----------
        wind_turbine_fleet : :obj:`list`
            List of dictionaries defining the wind turbine types and numbers
            of a wind farm. Dictionaries must have the following keys and
            corresponding values:

            * 'wind_turbine'
              Wind turbine type as :class:`~.powerplants.WindPowerPlant` or
              :obj:`dict` containing all turbine parameters required by the
              model :class:`~.models.WindpowerlibTurbine`
            * 'number_of_turbines'
              number of wind turbines

        Returns
        ----------
        :obj:`list`
            List of dictionaries defining the wind turbine types and numbers
            of a wind farm. Dictionaries has the following keys and
            corresponding values:

            * 'wind_turbine'
              Wind turbine type as :class:`~.powerplants.WindPowerPlant`
            * 'number_of_turbines'
              number of wind turbines

        """
        if isinstance(wind_turbine_fleet, list):
            # initialize wind turbines
            for turbine_dict in wind_turbine_fleet:
                turbine = turbine_dict['wind_turbine']
                if isinstance(turbine, feedinlib.powerplants.WindPowerPlant):
                    # check if model the turbine was instantiated with is
                    # WindpowerlibTurbine, otherwise instantiate new
                    # WindPowerPlant with WindpowerlibTurbine model
                    if not isinstance(turbine.model, WindpowerlibTurbine):
                        turbine = feedinlib.powerplants.WindPowerPlant(
                            **turbine.parameters)
                elif isinstance(turbine, dict):
                    # instantiate WindPowerPlant with WindpowerlibTurbine model
                    turbine = feedinlib.powerplants.WindPowerPlant(**turbine)
                else:
                    raise TypeError(
                        "The WindpowerlibTurbineCluster model requires that "
                        "wind turbines must either be provided as "
                        "WindPowerPlant objects or as dictionary containing "
                        "all turbine parameters required by the "
                        "WindpowerlibTurbine model.")
                turbine_dict['wind_turbine'] = turbine
        else:
            raise TypeError(
                "The WindpowerlibTurbineCluster model requires that the "
                "`wind_turbine_fleet` parameter is provided as a list but "
                "type of `wind_turbine_fleet` is {}.".format(
                    type(wind_turbine_fleet)))
        # @Günni diese Fkt. verändert das wind_turbine_fleet dict. ist das
        # zu undurchsichtig und es sollte besser returned werden oder ist es
        # auch ohne return okay?
        return wind_turbine_fleet

    def __repr__(self):
        return "WindpowerlibTurbineCluster"

    @property
    def powerplant_requires(self):
        r"""
        The parameters this model requires to set up a turbine cluster.

        In this feed-in model the required powerplant parameters are:

        :wind_turbine_fleet:
        :wind_farms:

        """
        required = ["wind_turbine_fleet", "wind_farms"]
        if super().powerplant_requires is not None:
            required.extend(super().powerplant_requires)
        return required

    def powerplant_requires_check(self, powerplant_parameters):
        r"""

        :param powerplant_parameters:
        :return:
        """
        if not any([_ in powerplant_parameters
                    for _ in self.powerplant_requires]):
            raise KeyError(
                "The specified model '{model}' requires one of the following "
                "power plant parameters: {parameters}".format(
                    model=self, parameters=self.powerplant_requires))

    @property
    def requires(self):
        r"""
        The parameters this model requires to calculate a feed-in.

        """
        required = []
        if super().requires is not None:
            required.extend(super().requires)
        return required

    @property
    def nominal_power_wind_power_plant(self):
        if self.powerplant:
            # ToDo Fix until fixed in windpowerlib
            #return self.windfarm.installed_power
            return self.powerplant.get_installed_power()
        else:
            return None

    def instantiate_windfarm(self, **kwargs):
        r"""
        Instantiates a windpowerlib WindFarm object

        Parameters
        ----------

        Returns
        --------
        :class:`windpowerlib.wind_farm.WindFarm`

        """
        # setup list of wind turbine fleet with windpowerlib's WindTurbine
        # objects to use in instantiation of WindFarm
        turbine_fleet = kwargs.pop('wind_turbine_fleet')
        turbine_list = []  # a new list is created in order to not change
                           # the original turbine fleet list
        for turbine_dict in turbine_fleet:
            turbine = turbine_dict['wind_turbine']
            turbine_list.append(
                {'wind_turbine': turbine.model.instantiate_turbine(
                    **turbine.parameters),
                 'number_of_turbines': turbine_dict['number_of_turbines']}
            )
        kwargs['wind_turbine_fleet'] = turbine_list

        # ToDo: fix until maybe solved in windpowerlib
        if 'name' not in kwargs.keys():
            kwargs['name'] = 'dummy_name'
        return WindpowerlibWindFarm(**kwargs)

    def instantiate_turbine_cluster(self, **kwargs):
        r"""
        Instantiates a windpowerlib WindTurbineCluster object

        Parameters
        ----------

        Returns
        --------
        :class:`windpowerlib.wind_turbine_cluster.WindTurbineCluster`

        """
        wind_farms = kwargs.pop('wind_farms')
        wind_farm_list = []  # a new list is created in order to not change the
                             # the original wind farm list
        for wind_farm in wind_farms:
            wind_farm_list.append(self.instantiate_windfarm(**wind_farm))
        kwargs['wind_farms'] = wind_farm_list

        # ToDo: fix until maybe solved in windpowerlib
        if 'name' not in kwargs.keys():
            kwargs['name'] = 'dummy_name'
        self.powerplant = WindpowerlibWindTurbineCluster(**kwargs)
        return self.powerplant

    def feedin(self, weather, power_plant_parameters, **kwargs):
        r"""
        Calculates feed-in of turbine cluster

        Parameters
        ----------
        weather : feedinlib Weather Object # @Günni, auch windpowerlibformat erlaubt?

        Returns
        --------

        """
        # ToDo Zeitraum einführen (time_span)
        # wind farm calculation
        if 'wind_turbine_fleet' in power_plant_parameters.keys():
            self.instantiate_turbine_cluster(
                **{'wind_farms': [power_plant_parameters]})
        # wind cluster calculation
        else:
            self.instantiate_turbine_cluster(**power_plant_parameters)
        mc = WindpowerlibClusterModelChain(self.powerplant, **kwargs)
        return mc.run_model(weather).power_output


if __name__ == "__main__":
    import doctest
    doctest.testmod()
