# -*- coding: utf-8 -*-
"""
@author: oemof development group
"""

from abc import ABC, abstractmethod
import os
import numpy as np
import pandas as pd
import pvlib
from windpowerlib import basicmodel as windmodel
import requests


class Base(ABC):
    r""" The base class of feedinlib models.

    Parameters
    ----------
    required : list of strings, optional
        Containing the names of the required parameters to use the model.

    """
    def __init__(self, **kwargs):
        self._required = kwargs.get("required")

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
        # Returning None rarely makes sense, IMHO.
        # Returning self at least allows for method chaining.
        return self


class PvlibBased(Base):
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
        self.area = None
        self.peak = None

    @property
    def required(self):
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
        if super().required is not None:
            return super().required
        return ["azimuth", "tilt", "module_name", "albedo"]

    def feedin(self, **kwargs):
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
        return self.get_pv_power_output(**kwargs).p_mp

    def solarposition_hourly_mean(self, location, data, **kwargs):
        r"""
        Determine the position of the sun as an hourly mean of all angles
        above the horizon.

        Parameters
        ----------
        location : pvlib.location.Location
            A pvlib location object containing the longitude, latitude and the
            timezone of the location
        data : pandas.DataFrame
            Containing the time index of the location.
        method : string, optional
            Method to calulate the position of the sun according to the
            methods provided by the pvlib function (default: 'ephemeris')
            'pvlib.solarposition.get_solarposition'. [2]_
        freq : string, optional
            The time interval to create the hourly mean (default: '5Min').

        pandas.DataFrame
            The DataFrame contains the following new columns: azimuth, zenith,
            elevation

        Notes
        -----
        Combining hourly values for irradiation with discrete values for the
        position of the sun can lead to unrealistic results. Using hourly
        values for the position minimizes these errors.

        References
        ----------
        .. [2] `pvlib solarposition <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#pvlib.solarposition.get_solarposition>`_.

        See Also
        --------
        solarposition : calculates the position of the sun at a given time
        """
        data_5min = pd.DataFrame(
            index=pd.date_range(data.index[0],
                                periods=data.shape[0]*12, freq='5Min',
                                tz=kwargs['weather'].timezone))

        data_5min = pvlib.solarposition.get_solarposition(
            time=data_5min.index, latitude=location.latitude,
            longitude=location.longitude, method='ephemeris')

        return pd.concat(
            [data, data_5min.clip_lower(0).resample('H').mean()],
            axis=1, join='inner')

    def solarposition(self, location, data, **kwargs):
        r"""
        Determine the position of the sun unsing the time of the time index.

        Parameters
        ----------
        location : pvlib.location.Location
            A pvlib location object containing the longitude, latitude and the
            timezone of the location
        data : pandas.DataFrame
            Containing the timeseries of the weather data and the time index of
            the location.
        method : string, optional
            Method to calulate the position of the sun according to the
            methods provided by the pvlib function (default: 'ephemeris')
            'pvlib.solarposition.get_solarposition'. [2]_

        Returns
        -------
        pandas.DataFrame
            The DataFrame contains the following new columns: azimuth, zenith,
            elevation

        Notes
        -----
        This method is not used in favour to solarposition_hourly_mean.

        Examples
        --------
        >>> import pvlib
        >>> import pandas as pd
        >>> from feedinlib import models
        >>> loc = pvlib.location.Location(52, 13, 'Europe/Berlin')
        >>> pvmodel = models.PvlibBased()
        >>> data = pd.DataFrame(index=pd.date_range(pd.datetime(2010, 1, 1, 0),
        ... periods=8760, freq='H', tz=loc.tz))
        >>> elevation = pvmodel.solarposition(loc, data).elevation
        >>> print(round(elevation[12], 3))
        14.968

        See Also
        --------
        solarposition_hourly_mean : calculates the position of the sun as an
            hourly mean.
        """
        return pd.concat(
            [data, pvlib.solarposition.get_solarposition(
                time=data.index, latitude=location.latitude,
                longitude=location.longitude,
                method=kwargs.get('method', 'ephemeris'))],
            axis=1, join='inner')

    def angle_of_incidence(self, data, **kwargs):
        r"""
        Determine the angle of incidence using the pvlib aoi funktion. [4]_

        Parameters
        ----------
        data : pandas.DataFrame
            Containing the timeseries of the azimuth and zenith angle
        tilt : float
            Tilt angle of the pv module (horizontal=0°).
        azimuth : float
            Azimuth angle of the pv module (south=180°).

        Returns
        -------
        pandas.Series
            Angle of incidence in degrees.

        See Also
        --------
        solarposition_hourly_mean, solarposition

        References
        ----------
        .. [4] `pvlib angle of incidence <http://pvlib-python.readthedocs.org/
                en/latest/pvlib.html#pvlib.irradiance.aoi>`_.
        """
        return pvlib.irradiance.aoi(
            solar_azimuth=data['azimuth'], solar_zenith=data['zenith'],
            surface_tilt=self.powerplant.tilt,
            surface_azimuth=self.powerplant.azimuth)

    def global_in_plane_irradiation(self, data, **kwargs):
        r"""
        Determine the global irradiaton on the tilted surface.

        This method determines the global irradiation in plane knowing
        the direct and diffuse irradiation, the incident angle and the
        orientation of the surface. The method uses the
        pvlib.irradiance.globalinplane function [5]_ and some other functions
        of the pvlib.atmosphere [6]_ and the pvlib.solarposition [2]_ module to
        provide the input parameters for the globalinplane function.

        Parameters
        ----------
        data : pandas.DataFrame
            Containing the time index of the location and columns with the
            following timeseries: (dirhi, dhi, zenith, azimuth, aoi)
        tilt : float
            Tilt angle of the pv module (horizontal=0°).
        azimuth : float
            Azimuth angle of the pv module (south=180°).
        albedo : float
            Albedo factor around the module

        Returns
        -------
        pandas.DataFrame
            The DataFrame contains the following new columns: poa_global,
            poa_diffuse, poa_direct

        References
        ----------
        .. [5] `pvlib globalinplane <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#pvlib.irradiance.globalinplane>`_.
        .. [6] `pvlib atmosphere <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#module-pvlib.atmosphere>`_.

        See Also
        --------
        solarposition_hourly_mean, solarposition, angle_of_incidenc
        """
        # Determine the extraterrestrial radiation
        data['dni_extra'] = pvlib.irradiance.extraradiation(
            datetime_or_doy=data.index.dayofyear)

        # Determine the relative air mass
        data['airmass'] = pvlib.atmosphere.relativeairmass(data['zenith'])

        # Determine direct normal irradiation
        data['dni'] = (data['dirhi']) / np.sin(np.radians(90 - data['zenith']))

        # what for??
        data['dni'][data['zenith'] > 88] = data['dirhi']

        # Determine the sky diffuse irradiation in plane
        # with model of Perez (modell switch would be good)
        data['poa_sky_diffuse'] = pvlib.irradiance.perez(
            surface_tilt=self.powerplant.tilt,
            surface_azimuth=self.powerplant.azimuth,
            dhi=data['dhi'],
            dni=data['dni'],
            dni_extra=data['dni_extra'],
            solar_zenith=data['zenith'],
            solar_azimuth=data['azimuth'],
            airmass=data['airmass'])

        # Set NaN values to zero
        data['poa_sky_diffuse'][
            pd.isnull(data['poa_sky_diffuse'])] = 0

        # Determine the diffuse irradiation from ground reflection in plane
        data['poa_ground_diffuse'] = pvlib.irradiance.grounddiffuse(
            ghi=data['dirhi'] + data['dhi'],
            albedo=self.powerplant.albedo,
            surface_tilt=self.powerplant.tilt)

        # Determine total in-plane irradiance
        data = pd.concat(
            [data, pvlib.irradiance.globalinplane(
                aoi=data['aoi'],
                dni=data['dni'],
                poa_sky_diffuse=data['poa_sky_diffuse'],
                poa_ground_diffuse=data['poa_ground_diffuse'])],
            axis=1, join='inner')

        return data

    def fetch_module_data(self, lib='sandia-modules', **kwargs):
        r"""
        Fetch the module data from the Sandia Module library

        The file is saved in the ~/.oemof folder and loaded from there to save
        time and to make it possible to work if the server is down.

        Parameters
        ----------
        module_name : string
            Name of a pv module from the sam.nrel database [9]_.

        Returns
        -------
        dictionary
            The necessary module data for the selected module to use the
            pvlib sapm pv model. [8]_

        Examples
        --------
        >>> from feedinlib import models
        >>> pvmodel = models.PvlibBased()
        >>> name = 'Yingli_YL210__2008__E__'
        >>> print(pvmodel.fetch_module_data(module_name=name).Area)
        1.7

        See Also
        --------
        pv_module_output
        """
        if kwargs.get('module_name') is None:
            kwargs['module_name'] = self.powerplant.module_name

        basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
        url = 'https://sam.nrel.gov/sites/default/files/'
        filename = os.path.join(basic_path, 'sam-library-sandia-modules.csv')
        if not os.path.exists(basic_path):
            os.makedirs(basic_path)
        if not os.path.isfile(filename):
            url_file = 'sam-library-sandia-modules-2015-6-30.csv'
            req = requests.get(url + url_file)
            with open(filename, 'wb') as fout:
                fout.write(req.content)
        if kwargs.get('module_name') == 'all':
            module_data = pvlib.pvsystem.retrieve_sam(path=filename)
        else:
            module_data = (pvlib.pvsystem.retrieve_sam(path=filename)
                           [kwargs['module_name']])
            self.area = module_data.Area
            self.peak = module_data.Impo * module_data.Vmpo
        return module_data

    def pv_module_output(self, data, **kwargs):
        r"""
        Determine the output of pv-system.

        Using the pvlib.pvsystem.sapm function of the pvlib [8]_.

        Parameters
        ----------
        module_name : string
            Name of a pv module from the sam.nrel database [9]_.
        data : pandas.DataFrame
            Containing the time index of the location and columns with the
            following timeseries: (temp_air [K], v_wind, poa_global,
            poa_diffuse, poa_direct, airmass, aoi)
        method : string, optional
            Method to calulate the position of the sun according to the
            methods provided by the pvlib function (default: 'ephemeris')
            'pvlib.solarposition.get_solarposition'. [10]_

        Returns
        -------
        pandas.DataFrame
            The DataFrame contains the following new columns: p_pv_norm,
            p_pv_norm_area

        References
        ----------
        .. [8] `pvlib pv-system <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#pvlib.pvsystem.sapm>`_.
        .. [9] `module library <https://sam.nrel.gov/sites/default/files/
                sam-library-sandia-modules-2015-6-30.csv>`_.
        .. [10] `pvlib get_solarposition <http://pvlib-python.readthedocs.org
                /en/latest/pvlib.html#pvlib.solarposition.get_solarposition>`_.

        See Also
        --------
        global_in_plane_irradiation
        """
        # Determine module and cell temperature
        data['temp_air_celsius'] = data['temp_air'] - 273.15
        data = pd.concat([data, pvlib.pvsystem.sapm_celltemp(
            poa_global=data['poa_global'],
            wind_speed=data['v_wind'],
            temp_air=data['temp_air_celsius'],
            model='Open_rack_cell_polymerback')], axis=1, join='inner')

        # Retrieve the module data object
        module_data = self.fetch_module_data(**kwargs)

        data['effective_irradiance'] = pvlib.pvsystem.sapm_effective_irradiance(
            poa_direct=data['poa_direct'], poa_diffuse=data['poa_diffuse'],
            airmass_absolute=data['airmass'], aoi=data['aoi'],
            module=module_data)

        # Apply the Sandia PV Array Performance Model (SAPM) to get a
        data = pd.concat([data, pvlib.pvsystem.sapm(
            effective_irradiance=data['effective_irradiance'],
            temp_cell=data['temp_cell'],
            module=module_data)], axis=1, join='inner')

        # Set NaN values to zero
        data['p_mp'][
            pd.isnull(data['p_mp'])] = 0
        return data

    def get_pv_power_output(self, **kwargs):
        r"""
        Output of the given pv module. For the theoretical background see the
        pvlib documentation [11]_.

        Parameters
        ----------
        weather : feedinlib.weather.FeedinWeather object
            Instance of the feedinlib weather object (see class
            :py:class:`FeedinWeather<feedinlib.weather.FeedinWeather>` for more
            details)

        Notes
        -----
        See :py:func:`method required <feedinlib.models.PvlibBased.required>`
        for all required parameters of this model.


        Returns
        -------
        pandas.DataFrame
            The DataFrame contains the following new columns: p_pv_norm,
            p_pv_norm_area and all timeseries calculated before.

        References
        ----------
        .. [11] `pvlib documentation <https://readthedocs.org/projects/
                pvlib-python/>`_.
        .. [12] `module library <https://sam.nrel.gov/sites/default/files/
                sam-library-sandia-modules-2015-6-30.csv>`_.

        See Also
        --------
        pv_module_output, feedin
        """
        data = kwargs['weather'].data

        # Create a location object
        location = pvlib.location.Location(kwargs['weather'].latitude,
                                           kwargs['weather'].longitude,
                                           kwargs['weather'].timezone)

        # Determine the position of the sun
        data = self.solarposition_hourly_mean(location, data, **kwargs)

        # A zenith angle greater than 90° means, that the sun is down.
        data['zenith'][data['zenith'] > 90] = 90

        # Determine the angle of incidence
        data['aoi'] = self.angle_of_incidence(data, **kwargs)

        # Determine the irradiation in plane
        data = self.global_in_plane_irradiation(data, **kwargs)

        # Determine the output of the pv module
        data = self.pv_module_output(data, **kwargs)

        return data


class SimpleWindTurbine(Base):
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

    @property
    def required(self):
        r""" The parameters this model requires to calculate a feedin.

        In this feedin model the required parameters are:

        :h_hub: (float) -
            Height of the hub of the wind turbine
        :d_rotor: (float) -
            'Diameter of the rotor [m]',
        :wind_conv_type: (string) -
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.
        """

        if super().required is not None:
            return super().required
        return ["h_hub", "d_rotor", "wind_conv_type"]

    def feedin(self, **kwargs):
        r"""
        Alias for :py:func:`turbine_power_output
        <feedinlib.models.SimpleWindTurbine.turbine_power_output>`.
        """
        my_turbine = windmodel.SimpleWindTurbine(
            wind_conv_type=kwargs.pop('wind_conv_type'),
            h_hub=kwargs.pop('h_hub'), d_rotor=kwargs.pop('d_rotor'))
        self.nominal_power_wind_turbine = my_turbine.nominal_power
        return my_turbine.turbine_power_output(
            weather=kwargs['weather'].data,
            data_height=kwargs['weather'].data_height)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
