# -*- coding: utf-8 -*-
"""
@author: oemof developing group

Classes in this module correspond to specific types of powerplants.

Powerplant objects act as data holders for the attributes making up a
powerplants specification. These objects should only contain little logic.
Computing the actual feedin provided by a powerplant is done using it's `model`
attribute.`
"""

from abc import ABC, abstractmethod

from feedinlib.models import Pvlib, WindpowerlibTurbine


class Base(ABC):

    def __init__(self, **attributes):
        r""" The base class of feedinlib powerplants.

        The most prominent shared functionality between powerplants is the fact
        that they instantiate their model class upon construction, in order to
        get a unique model instance for each powerplant instance.

        Parameters
        ----------
        model : A model class or an instance of one
          If a class (or in general, any instance of :class:`type`) is
          provided, it is used to create the model instance encapsulating the
          actual mathematical model used to calculate the feedin provided by
          this powerplant.

          In any other case, the provided object is used directly. Note though,
          that a reference to this powerplant is saved in the provided object,
          so sharing model instances between two powerplant objects is not a
          good idea, as the second powerplant will overwrite the reference the
          reference to the first.

          The non-class version is only provided for users who need the extra
          flexibility of controlling model instantiation and who know what they
          are doing. In general, you'll want to provide a class for this
          parameter or just go with the default for the specific subclass you
          are using.

        \**attributes :
          The remaining attributes providing the technical specification of
          the powerplant. They will be added as regular attributes to this
          object, with keys as attribute names and initialized to the
          corresponding values.

          An error is raised if the attributes required by the given model are
          not contained in this hash.

        Raises
        ------
        AttributeError
            in case the attribute listed in the given model's required
            attribute are not present in the `attributes` parameter.

        See Also
        --------
        :mod:`feedinlib.models` : for and explanation of the model needed to
                                  actually calculate the feedin.

        """
        model = attributes.pop("model")
        if isinstance(model, type):
            model = model()
        self.model = model

        self.parameters = attributes

        # check if all power plant attributes required by the respective model
        # are provided
        parameters_keys = attributes.keys()
        for k in self.required:
            if k not in parameters_keys:
                raise KeyError(
                    "The specified model '{model}' requires power plant "
                    "parameter '{k}' but it's not provided as an "
                    "argument.".format(k=k, model=model))

    @abstractmethod
    def feedin(self, weather, **kwargs):
        r"""
        Calculates the amount of energy fed in by this powerplant into the
        energy system.

        This method delegates the actual computation to the :meth:`feedin`
        method of this objects :attr:`model` while giving you the opportunity
        to override some of the inputs used to calculate the feedin.

        benötigt wetterdaten

        Parameters
        ----------
        weather : feedinlib weather data object
            weather data to calculate feedin with
        \**kwargs :
            Keyword arguments for respective model's feedin calculation. Can
            also be used to overwrite the model feedin is calculated with.

        Returns
        -------
        feedin : Pandas dataframe
          The feedin provided by this poweplant as a time series represented
          by a :py:class:`pandas.DataFrame`.

        """
        # @Günni: sollte model hier überschrieben werden?
        # TODO: Document semantics of special keyword arguments.
        model = self.model

        # required power plant arguments are checked again in case a different
        # model to calculate feedin is used than initially specified
        combined = {}
        for k in self.required:
            if k not in self.parameters:
                raise AttributeError(
                    "The specified model '{model}' requires power plant "
                    "parameter '{k}' but it's not provided as an "
                    "argument.".format(k=k, model=model))
            else:
                combined[k] = self.parameters[k]

        # check if all arguments required by the feedin model are given
        keys = kwargs.keys()
        for k in model.requires:
            if not k in keys:
                raise AttributeError(
                    "The specified model '{model}' requires model "
                    "parameter '{k}' but it's not provided as an "
                    "argument.".format(k=k, model=model))
        return model.feedin(weather=weather,
                            power_plant_parameters=self.parameters, **kwargs)

    @property
    @abstractmethod
    def required(self):
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
        return []


class Photovoltaic(Base):

    def __init__(self, model=Pvlib, **attributes):
        r"""
        Photovoltaic objects correspond to powerplants using solar power to
        generate electricity.

        Parameters
        ----------
        model :
          Used as the `model` parameter for :class:`Base`.
          Defaults to :class:`feedinlib.models.PvlibBased`.
        \**attributes : see :class:`Base`
        """
        super().__init__(model=model, **attributes)

    def feedin(self, weather, scaling=None, scaling_value=1, **kwargs):
        feedin = super().feedin(weather=weather, **kwargs)
        if scaling:
            feedin_scaling = {
                'peak_power': lambda feedin, scaling_value: feedin / float(
                    self.peak_power) * scaling_value,
                'area': lambda feedin, scaling_value: feedin / float(
                    self.area) * scaling_value}
            return feedin_scaling[scaling](feedin, scaling_value)
        return feedin

    @property
    def required(self):
        r""" The PV system parameters the specified model requires.

        Check powerplant_requires
        """
        required = self.model.powerplant_requires
        if super().required is not None:
            required.extend(super().required)
        return required

    @property
    def area(self):
        return self.model.pv_system_area

    @property
    def peak_power(self):
        return self.model.pv_system_peak_power


class WindPowerPlant(Base):
    def __init__(self, model=WindpowerlibTurbine, **attributes):
        r"""
        WindPowerPlant objects correspond to powerplants using wind power to
        generate electricity.

        Parameters
        ----------
        model :
          Used as the model argument for :class:`Base`.
          Defaults to :class:`feedinlib.models.SimpleWindTurbine`.
        \**attributes : See :class:`Base`
        See Also
        --------
        :mod:`feedinlib.models` : for and explanation of the model needed to
                                  actually calculate the feedin.
        """
        super().__init__(model=model, **attributes)

    @property
    def required(self):
        r""" The wind turbine parameters the specified model requires.
        """
        required = self.model.powerplant_requires
        if super().required is not None:
            required.extend(super().required)
        return required

    def feedin(self, weather, scaling=None, scaling_value=1, **kwargs):
        feedin = super().feedin(weather, **kwargs)
        if scaling:
            feedin_scaling = {
                'capacity': lambda feedin, scaling_value: feedin / float(
                    self.nominal_power) * scaling_value,
                'number': lambda feedin, scaling_value: feedin * scaling_value}
            return feedin_scaling[scaling](feedin, scaling_value)
        return feedin

    @property
    def nominal_power(self):
        return self.model.nominal_power_wind_power_plant
