# -*- coding: utf-8 -*-
"""
@author: oemof development group
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

    Parameters
    ----------
    required : list of strings, optional
        Containing the names of the required parameters to use the model.

    """
    def __init__(self, **kwargs):
        self._powerplant_requires = kwargs.get("powerplant_requires")

    @property
    @abstractmethod
    def powerplant_requires(self):
        """ The (names of the) parameters this model requires in order to
        calculate the feedin.

        As this is an abstract property, you have to override it in a subclass
        so that the model can be instantiated. This forces implementors to make
        the required parameters for a model explicit, even if they are empty,
        and gives them a good place to document them.

        By default, this property is settable and its value can be specified
        via and argument on construction. If you want to keep this
        functionality, simply delegate all calls to the superclass.
        """
        return self._powerplant_requires

    @powerplant_requires.setter
    def powerplant_requires(self, names):
        # Returning None rarely makes sense, IMHO.
        # Returning self at least allows for method chaining.
        self._powerplant_requires = names
        return self

    @property
    @abstractmethod
    def model_requires(self):
        """ The (names of the) parameters this model requires in order to
        calculate the feedin.

class Pvlib(Base):
        """
        return self._model_requires

    @model_requires.setter
    def model_requires(self, names):
        self._model_requires = names
        return self
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
        # Todo kann hier Instanziierung des PV Systems erfolgen?
        # ToDo Nach Instanziierung area und peak setzen (wie kann ich von hier auf Photovoltaic zugreifen?

    def __repr__(self):
        return "pvlib"

    @property
    def powerplant_requires(self):
        r""" The parameters this model requires to calculate a feedin.

        In this feedin model the required parameters are:

        :modul_name: (string) -
            name of a pv module from the sam.nrel database [12]_
        :tilt: (float) -
            tilt angle of the pv module (horizontal=0°)
        :azimuth: (float) -
            azimuth angle of the pv module (south=180°)
        :albedo: (float) -
            albedo factor arround the module
        """
        # ToDo maybe add method to assign suitable inverter if none is specified
        if super().powerplant_requires is not None:
            return super().powerplant_requires
        return ["azimuth", "tilt", "module_name", "albedo", "inverter_name"]

    # @Günni: wie festhalten, dass es eine notwendige property für PV ist? Neue abstrakte Klasse einführen?
    # ToDo: bei parallelen Strängen area anders berechnen?
    @property
    def module_area(self):
    def model_requires(self):
        r""" The parameters this model requires to calculate a feedin.

        """
        # @Günni wozu wird das gemacht?
        if super().powerplant_requires is not None:
            return super().powerplant_requires
        return []
        if self.module:
            return self.module.module_parameters.Area
        else:
            return None

    @property
    def module_peak_power(self):
        if self.module:
            return self.module.module_parameters.Impo * \
                   self.module.module_parameters.Vmpo
        else:
            return None

    def instantiate_module(self):
        #ToDo könnten weitere Parameter übergeben werden?
        module = {
            'module_parameters': self.get_module_data()[self.powerplant.module_name],
            'inverter_parameters': self.get_converter_data()[self.powerplant.inverter_name],
            'surface_azimuth': self.powerplant.azimuth,
            'surface_tilt': self.powerplant.tilt,
            'albedo': self.powerplant.albedo,
        }
        self.module = PvlibPVSystem(**module)
        return self.module

    def feedin(self, weather, location, **kwargs):
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

        mc = PvlibModelChain(self.instantiate_module(),
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


class WindpowerlibTurbine(Base):
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
        self.nominal_power_wind_turbine = None

    def __repr__(self):
        return "windpowerlib"

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

        if super().powerplant_requires is not None:
            return super().powerplant_requires
        return ["hub_height", "name"]

    @property
    def turbine_nominal_power(self):
    def model_requires(self):
        r""" The parameters this model requires to calculate a feedin.

        """
        if super().powerplant_requires is not None:
            return super().powerplant_requires
        return []

        if self.turbine:
            return self.turbine.nominal_power
        else:
            return None

    def instantiate_turbine(self):
        # ToDo: weitere kwargs zulassen
        turbine = {
            'name': self.powerplant.name,
            'hub_height': self.powerplant.hub_height,
            'fetch_curve': self.powerplant.fetch_curve
        }
        self.turbine = WindpowerlibWindTurbine(**turbine)
        return self.turbine

    def feedin(self, weather, **kwargs):
        r"""
        Alias for :py:func:`turbine_power_output
        <feedinlib.models.SimpleWindTurbine.turbine_power_output>`.

        weather : feedinlib Weather Object # @Günni, auch windpowerlibformat erlaubt?
        """
        # ToDo Zeitraum einführen (time_span)
        return WindpowerlibModelChain(self.instantiate_turbine()).run_model(
            weather).power_output


if __name__ == "__main__":
    import doctest
    doctest.testmod()
