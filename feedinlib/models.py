# -*- coding: utf-8 -*-
"""
@author: oemof developer group
"""

from abc import ABC, abstractmethod

# windpowerlib
from windpowerlib.modelchain import ModelChain as WindpowerlibModelChain
from windpowerlib.wind_turbine import WindTurbine as WindpowerlibWindTurbine

# pvlib
from pvlib.modelchain import ModelChain as PvlibModelChain
from pvlib.pvsystem import PVSystem as PvlibPVSystem
from pvlib.location import Location as PvlibLocation
import pvlib.pvsystem


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
        self.module = None

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
        if self.module:
            return self.module.module_parameters.Area * \
                   self.module.strings_per_inverter * \
                   self.module.modules_per_string
        else:
            return None

    @property
    def pv_system_peak_power(self):
        if self.module:
            return self.module.module_parameters.Impo * \
                   self.module.module_parameters.Vmpo * \
                   self.module.strings_per_inverter * \
                   self.module.modules_per_string
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
        self.module = PvlibPVSystem(**kwargs)
        return self.module

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
        self.turbine = None

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
        if self.turbine:
            return self.turbine.nominal_power
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
        self.turbine = WindpowerlibWindTurbine(**kwargs)
        return self.turbine

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
    r"""Model to determine the output of a wind turbine cluster

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
        self.turbine_cluster = None
        self.windfarm = None
        # windfarm
        if 'wind_turbine_fleet' in kwargs.keys():
            # initialize wind turbines
            for turbine_dict in kwargs['wind_turbine_fleet']:
                turbine = turbine_dict['wind_turbine']
                if isinstance(turbine, feedinlib.powerplants.WindPowerPlant):
                    #check if model turbine was instantiated with is WindpowerlibTurbine
                    # otherwise instantiate new WindPowerPlant with WindpowerlibTurbine model
                    if not isinstance(turbine.model, WindpowerlibTurbine):
                        turbine = feedinlib.powerplants.WindPowerPlant(**turbine.parameters)
                elif isinstance(turbine, dict):
                    # instantiate turbine and add to windfarm
                    turbine = feedinlib.powerplants.WindPowerPlant(**turbine)
                else:
                    raise AttributeError(
                        "The WindpowerlibTurbineCluster model requires that "
                        "wind turbines must either be provided as "
                        "WindPowerPlant objects or as dictionary containing "
                        "all turbine parameters required by the "
                        "WindpowerlibTurbine model.")
                turbine_dict['wind_turbine'] = turbine

    def __repr__(self):
        return "windpowerlib_turbine_cluster"

    @property
    def powerplant_requires(self):
        r""" The parameters this model requires to set up a turbine cluster.

        In this feedin model the required parameters are:

        :h_hub: (float) -
            Height of the hub of the wind turbine
        :wind_conv_type: (string) -
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.
        """
        required = ["wind_turbine_fleet"]
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
        if self.windfarm:
            # ToDo Fix until fixed in windpowerlib
            #return self.windfarm.installed_power
            return self.windfarm.get_installed_power()
        else:
            return None

    def instantiate_windfarm(self, **kwargs):
        # setup list of wind turbine fleet with windpowerlib's WindTurbine
        # objects to use in instantiation of WindFarm
        turbine_fleet = kwargs.pop('wind_turbine_fleet')
        turbine_list = []  # a new list is created in order to not change the
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
        self.windfarm = WindpowerlibWindFarm(**kwargs)
        return self.windfarm

    def feedin(self, weather, power_plant_parameters, **kwargs):
        r"""
        Alias for :py:func:`turbine_power_output
        <feedinlib.models.SimpleWindTurbine.turbine_power_output>`.

        weather : feedinlib Weather Object # @Günni, auch windpowerlibformat erlaubt?
        """
        # ToDo Zeitraum einführen (time_span)
        self.instantiate_windfarm(**power_plant_parameters)
        mc = WindpowerlibClusterModelChain(
            self.instantiate_windfarm(**power_plant_parameters), **kwargs)
        return mc.run_model(weather).power_output


if __name__ == "__main__":
    import doctest
    doctest.testmod()
