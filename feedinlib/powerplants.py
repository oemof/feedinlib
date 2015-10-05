#! /usr/bin/env python
""" Classes in this module correspond to specific types of powerplants.

Powerplant objects act as data holders for the attributes making up a
powerplants specification. These objects should only contain little logic.
Computing the actual feedin provided by a powerplant is done using it's `model`
attribute.`
"""
from . import models


class Photovoltaic:
    def __init__(self, model=models.Photovoltaic([]), **attributes):
        r"""
        Photovoltaic objects correspond to powerplants using solar power to
        generate electricity.

        Parameters
        ----------
        model :
          An object encapsulating the actual mathematical model used to
          calculate the feedin provided by this powerplant.

          Defaults to an instance of :class:`feedinlib.models.Photovoltaic`
          with no requirements on the attributes needed to calculate the
          feedin.
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
        model.powerplant = self
        self.model = model
        for k in attributes:
            setattr(self, k, attributes[k])
        for k in model.required:
            if not hasattr(self, k):
                raise AttributeError(
                    "Your model requires {k}".format(k=k) +
                    " but it's not provided as an argument.")

    def feedin_as_list(self, **kwargs):
        r"""
        Works as :py:func:`feedin<feedinlib.powerplants.Photovoltaic.feedin>`
        but returns a list.

        Returns
        -------
        feedin : list
            The feedin provided by this poweplant as a time series.
        """
        return list(self.feedin_as_pd(**kwargs))

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
            feedin_pd = self.model.feedin(**combined) * kwargs['number']
        elif kwargs.get('peak_power', None) is not None:
            feedin_pd = (self.model.feedin(**combined) / self.model.peak *
                         10 ** 3 * kwargs['peak_power'])
        elif kwargs.get('area', None) is not None:
            feedin_pd = (self.model.feedin(**combined) / self.model.area *
                         kwargs['area'])
        else:
            feedin_pd = self.model.feedin(**combined)

        return feedin_pd


class WindPowerPlant:
    def __init__(self, model=models.WindPowerPlant([]), **attributes):
        r"""
        WindPowerPlant objects correspond to powerplants using wind power to
        generate electricity.

        Parameters
        ----------
        model :
          An object encapsulating the actual mathematical model used to
          calculate the feedin provided by this powerplant.

          Defaults to an instance of :class:`feedinlib.models.WindPowerPlant`
          with no requirements on the attributes needed to calculate the
          feedin.
        \**attributes : hash
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
        model.powerplant = self
        self.model = model
        for k in attributes:
            setattr(self, k, attributes[k])
        for k in model.required:
            if not hasattr(self, k):
                raise AttributeError(
                    "Your model requires {k}".format(k=k) +
                    " but it's not provided as an argument.")

    def feedin_as_list(self, **kwargs):
        r"""
        Works as :py:func:`feedin<feedinlib.powerplants.WindPowerPlant.feedin>`
        but returns a list.

        Returns
        -------
        feedin : list
            The feedin provided by this poweplant as a time series.
        """
        return list(self.feedin(**kwargs))

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
        combined = {k: getattr(self, k) for k in self.model.required}
        combined.update(kwargs)
        if kwargs.get('number', None) is not None:
            feedin_pd = self.model.feedin(**combined) * kwargs['number']
        elif kwargs.get('installed_capacity', None) is not None:
            feedin_pd = (self.model.feedin(**combined) /
                         float(self.model.nominal_power_wind_turbine) *
                         kwargs['installed_capacity'])
        else:
            feedin_pd = self.model.feedin(**combined)
        return feedin_pd
