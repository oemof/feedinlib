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

from . import models


class Base(ABC):
    # TODO: properly link/highlight the terms model and powerplant as they are
    #       referring to feedinlib internals.
    def __init__(self, **attributes):
        r""" The base class of feedinlib powerplants.

        The most prominent shared functionality between powerplants is the fact
        that they instantiate their model class uppon construction, in order to
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
        model.powerplant = self
        self.model = model
        for k in attributes:
            setattr(self, k, attributes[k])
        for k in model.required:
            if not hasattr(self, k):
                raise AttributeError(
                    "Your model requires {k}".format(k=k) +
                    " but it's not provided as an argument.")

    @abstractmethod
    def feedin(self, **kwargs):
        r"""
        Calculates the amount of energy fed in by this powerplant into the
        energy system.

        This method delegates the actual computation to the :meth:`feedin`
        method of this objects :attr:`model` while giving you the opportunity
        to override some of the inputs used to calculate the feedin.

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
        # TODO: Document semantics of special keyword arguments.
        combined = {k: getattr(self, k) for k in self.model.required}
        combined.update(kwargs)
        if kwargs.get('number', None) is not None:
            feedin = self.model.feedin(**combined) * kwargs['number']
        elif kwargs.get('peak_power', None) is not None:
            feedin = (self.model.feedin(**combined) /
                      float(self.model.peak) *
                      float(kwargs['peak_power']))
        elif kwargs.get('area', None) is not None:
            feedin = (self.model.feedin(**combined) / self.model.area *
                      kwargs['area'])
        elif kwargs.get('installed_capacity', None) is not None:
            feedin = (self.model.feedin(**combined) /
                      float(self.model.nominal_power_wind_turbine) *
                      float(kwargs['installed_capacity']))
        else:
            feedin = self.model.feedin(**combined)

        return feedin


class Photovoltaic(Base):
    def __init__(self, model=models.PvlibBased, **attributes):
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

    def feedin(self, **kwargs):
        return super().feedin(**kwargs)


class WindPowerPlant(Base):
    def __init__(self, model=models.SimpleWindTurbine, **attributes):
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

    def feedin(self, **kwargs):
        return super().feedin(**kwargs)
