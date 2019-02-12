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
        self._required = attributes.get("required")
        # Günni? ermöglicht das, eine oemof Klasse zu übergeben? Nein, erst Feedin Klasse
        model = attributes.pop("model")
        if isinstance(model, type):
            model = model()
        model.powerplant = self  # Günni, wieso wird das gemacht? - Evtl. raus nehmen um keine zyklischen Abhängigkeiten zu haben
        self.model = model
        for k in attributes:
            setattr(self, k, attributes[k])
        for k in self.required:
            if not hasattr(self, k):
                raise AttributeError(
                    "Your model requires {k}".format(k=k) +
                    " but it's not provided as an argument.")

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
        \**kwargs :
          Keyword arguments. If not specified, all the paramters needed to
          calculate the feedin are taken from this object. If any keyword
          argument is present whose key matches one of the parameters needed
          to calculate the feedin, it takes precedence over a matching
          attribute of this object.

        Returns
        -------
        feedin : Pandas dataframe
          The feedin provided by this poweplant as a time series represented
          by a :py:class:`pandas.DataFrame`.

        """
        # @Günni: sollte model hier überschrieben werden?
        # TODO: Document semantics of special keyword arguments.

        # required power plant arguments are checked again in case a different
        # model to calculate feedin is used than initially specified
        combined = {}
        for k in self.model.powerplant_requires:
            if not hasattr(self, k):
                raise AttributeError(
                    "The specified model '{model}' requires power plant "
                    "parameter '{k}' but it's not provided as an "
                    "argument.".format(k=k, model=self.model))
            else:
                combined[k] = getattr(self, k)
        # initially specified power plant parameters are over-written by kwargs
        # which is e.g. useful for parameter variations
        combined.update(kwargs)
        return self.model.feedin(weather=weather, **combined)

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
        return self._required

    @required.setter
    def required(self, names):
        self._required = names
        return self


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
        r""" The module parameters the specified model requires.

        Check powerplant_requires
        """
        if super().required is not None:
            return super().required
        return self.model.powerplant_requires

    @property
    def area(self):
        return self.model.module_area

    @property
    def peak_power(self):
        return self.model.module_peak_power


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
        if super().required is not None:
            return super().required
        return self.model.powerplant_requires

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
        return self.model.turbine_nominal_power
