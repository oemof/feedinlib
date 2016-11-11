# -*- coding: utf-8 -*-
"""
@author: oemof development group
"""

from abc import ABC, abstractmethod
import os
import sys
import numpy as np
import pandas as pd
import pvlib
import logging
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
            Albedo factor arround the module

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
        return self.turbine_power_output(**kwargs)

    def get_wind_pp_types(self, print_out=True):
        r"""
        Get the names of all possible wind converter types.

        Parameters
        ----------
        print_out : boolean (default: True)
            Directly prints the list of types if set to True.

        Examples
        --------
        >>> from feedinlib import models
        >>> w_model = models.SimpleWindTurbine()
        >>> valid_types_df = w_model.get_wind_pp_types(print_out=False)
        >>> valid_types_df.shape
        (91, 2)
        """
        res_df, df = self.fetch_cp_values_from_file(wind_conv_type='')

        if print_out:
            pd.set_option('display.max_rows', len(df))
            print(df[['rli_anlagen_id', 'p_nenn']])
            pd.reset_option('display.max_rows')
        return df[['rli_anlagen_id', 'p_nenn']]

    def rho_hub(self, weather):
        r"""
        Calculates the density of air in kg/m³ at hub height.
            (temperature in K, height in m, pressure in Pa)

        Parameters
        ----------
        data : DataFrame or Dictionary
            Containing columns or keys with the timeseries for Temperature
            (temp_air) and pressure (pressure).
        data_height : DataFrame or Dictionary
            Containing columns or keys with the height of the measurement or
            model data for temperature (temp_air) and pressure (pressure).
        h_hub : float
            Height of the hub of the wind turbine

        Returns
        -------
        float
            density of air in kg/m³ at hub height

        Notes
        -----
        Assumptions:
          * Temperature gradient of -6.5 K/km
          * Pressure gradient of -1/8 hPa/m

        The following equations are used [22]_:

        .. math:: T_{hub}=T_{air, data}-0.0065\cdot\left(h_{hub}-h_{T,data}
            \right)
        .. math:: p_{hub}=\left(p_{data}/100-\left(h_{hub}-h_{p,data}\right)
            *\frac{1}{8}\right)/\left(2.8706\cdot T_{hub}\right)

        with T: temperature [K], h: height [m], p: pressure [Pa]

        ToDo: Check the equation and add references.

        References
        ----------
        .. [22] ICAO-Standardatmosphäre (ISA).
            http://www.deutscher-wetterdienst.de/lexikon/download.php?file=Standardatmosphaere.pdf

        See Also
        --------
        v_wind_hub
        """
        h_temperature_data = weather.data_height['temp_air']
        h_pressure_data = weather.data_height['pressure']
        T_hub = weather.data.temp_air - 0.0065 * (
            self.powerplant.h_hub - h_temperature_data)
        return (
            weather.data.pressure / 100 -
            (self.powerplant.h_hub - h_pressure_data) * 1 / 8
            ) / (2.8706 * T_hub)

    def v_wind_hub(self, weather):
        r"""
        Calculates the wind speed in m/s at hub height.

        Parameters
        ----------
        data : DataFrame or Dictionary
            Containing columns or keys with the timeseries for wind speed
            (v_wind) and roughness length (z0).
        data_height : DataFrame or Dictionary
            Containing columns or keys with the height of the measurement or
            model data for temperature (temp_air) and pressure (pressure).
        h_hub : float
            Height of the hub of the wind turbine

        Returns
        -------
        float
            wind speed [m/s] at hub height

        Notes
        -----
        The following equation is used for the logarithmic wind profile [20]_:

        .. math:: v_{wind,hub}=v_{wind,data}\cdot\frac{\ln\left(\frac{h_{hub}}
            {z_{0}}\right)}{\ln\left(\frac{h_{data}}{z_{0}}\right)}

        with:
            v: wind speed [m/s], h: height [m], z0: roughnes length [m]

        :math:`h_{data}` is the hight in which the wind velocity is measured.
        (height in m, velocity in m/s)

        ToDo: Check the equation and add references.

        References
        ----------
        .. [20] Gasch R., Twele J.: "Windkraftanlagen". 6. Auflage, Wiesbaden,
                Vieweg + Teubner, 2010, page 129

        See Also
        --------
        rho_hub
        """
        return (weather.data.v_wind * np.log(self.powerplant.h_hub /
                weather.data.z0) /
                np.log(weather.data_height['v_wind'] /
                weather.data.z0))

    def fetch_cp_values_from_file(self, **kwargs):
        r"""
        Fetch cp values from a file or download it from a server.

        The files are located in the ~/.oemof folder.

        Parameters
        ----------
        wind_conv_type : string
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.
        cp_path : string, optional
            Path where the cp file is stored
        filename : string, optional
            Filename of the cp file without suffix. The suffix should be csv or
            hf5.
        url : string, optional
            URL from where the cp file is loaded if not present

        Returns
        -------
        pandas.DataFrame
            cp values, wind converter type, installed capacity or the full
            table if the given wind converter cannot be found in the table.

        Notes
        -----
        The files can be downloaded from
        http://vernetzen.uni-flensburg.de/~git/

        See Also
        --------
        fetch_cp_values_from_db
        """
        wpp_type = kwargs.get('wind_conv_type')
        if wpp_type is None:
            wpp_type = self.powerplant.wind_conv_type
        cp_path = kwargs.get(
            'basic_path', os.path.join(os.path.expanduser("~"), '.oemof'))
        filename = kwargs.get('filename', 'cp_values')
        filepath = os.path.join(cp_path, filename)
        url = kwargs.get(
            'url', 'http://vernetzen.uni-flensburg.de/~git/cp_values')
        suffix = '.hf5'
        if not os.path.exists(cp_path):
            os.makedirs(cp_path)
        if not os.path.isfile(filepath + suffix):
            req = requests.get(url + suffix)
            with open(filepath + suffix, 'wb') as fout:
                fout.write(req.content)
            logging.info('Copying cp_values from {0} to {1}'.format(
                url, filepath + suffix))
        logging.debug('Retrieving cp values from {0}'.format(
            filename + suffix))
        try:
            df = pd.read_hdf(filepath + suffix, 'cp')
        except:
            suffix = '.csv'
            logging.info('Failed loading cp values from hdf file, trying csv.')
            logging.debug('Retrieving cp values from {0}'.format(
                filename + suffix))
            if not os.path.isfile(filename + suffix):
                req = requests.get(url + suffix)
                with open(filepath + suffix, 'wb') as fout:
                    fout.write(req.content)
                logging.info('Copying cp_values from {0} to {1}'.format(
                    url, filename + suffix))
            df = pd.read_csv(filename + suffix, index_col=0)
        res_df = df[df.rli_anlagen_id == wpp_type].reset_index(drop=True)
        return res_df, df

    def fetch_cp_values(self, **kwargs):
        r"""
        Fetch cp values from database, file or http source.

        If no set of cp values is given, tries to fetch the values from the
        database. If no valid database connection is present, tries to read the
        values from a local file. If the need files are not present, loads the
        files from a server. First tries to read the hdf5 file and then the csv
        file.

        Parameters
        ----------
        wind_conv_type : string
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.

        Returns
        -------
        pandas.DataFrame
            cp values, wind converter type, installed capacity

        Examples
        --------
        >>> from feedinlib import models
        >>> w_model = models.SimpleWindTurbine()
        >>> cp = w_model.fetch_cp_values(wind_conv_type='ENERCON E 126 7500')
        >>> index=cp.loc[0, :][2:55].index=='8'
        >>> print(cp.loc[0, :][2:55].values[index][0])
        0.478

        See Also
        --------
        fetch_cp_values_from_db, fetch_cp_values_from_file
        """
        if kwargs.get('cp_values', None) is not None:
            res_df = kwargs.get['cp_values']
        else:
            res_df, df = self.fetch_cp_values_from_file(**kwargs)

        if res_df.shape[0] == 0:
            pd.set_option('display.max_rows', len(df))
            logging.info('Possible types: \n{0}'.format(df.rli_anlagen_id))
            pd.reset_option('display.max_rows')
            res_df = df
            sys.exit('Cannot find the wind converter typ: {0}'.format(
                kwargs.get('wind_conv_type', None)))
        return res_df

    def cp_values(self, v_wind, **kwargs):
        r"""
        Interpolates the cp value as a function of the wind velocity between
        data obtained from the power curve of the specified wind turbine type.

        Parameters
        ----------
        wind_conv_type : string
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.
        v_wind : pandas.Series or numpy.array
            Wind speed at hub height [m/s]

        Returns
        -------
        numpy.array
            cp values, wind converter type, installed capacity


        >>> from feedinlib import models
        >>> import numpy
        >>> v_wi = numpy.array([1,2,3,4,5,6,7,8])
        >>> w = models.SimpleWindTurbine(required=['wind_conv_type', 'v_wind'])
        >>> cp = w.cp_values(wind_conv_type='ENERCON E 126 7500', v_wind=v_wi)
        >>> print(cp)
        [ 0.     0.     0.191  0.352  0.423  0.453  0.47   0.478]

        See Also
        --------
        fetch_cp_values_from_db, fetch_cp_values_from_file
        """
        ncols = ['rli_anlagen_id', 'p_nenn', 'source', 'modificationtimestamp']
        res_df = self.fetch_cp_values(**kwargs)
        cp_data = np.array([0, 0])
        for col in res_df.keys():
            if col not in ncols:
                if res_df[col][0] is not None and not np.isnan(
                        float(res_df[col][0])):
                    cp_data = np.vstack((cp_data, np.array(
                        [float(col), float(res_df[col])])))
        cp_data = np.delete(cp_data, 0, 0)
        self.nominal_power_wind_turbine = res_df['p_nenn'][0] * 1000
        v_wind[v_wind > np.max(cp_data[:, 0])] = np.max(cp_data[:, 0])
        return np.interp(v_wind, cp_data[:, 0], cp_data[:, 1])

    def turbine_power_output(self, **kwargs):
        r"""
        Calculates the power output in W of one wind turbine.

        Parameters
        ----------
        weather : feedinlib.weather.FeedinWeather object
            Instance of the feedinlib weather object (see class
            :py:class:`FeedinWeather<feedinlib.weather.FeedinWeather>` for more
            details)
        \**kwargs :
            Keyword arguments for underlaying methods like filename to name the
            file of the cp_values.
        # TODO Move the following parameters to a better place :-)

        Returns
        -------
        pandas.Series
            Electrical power of the wind turbine

        Notes
        -----
        The following equation is used for the power output :math:`P_{wpp}`
        [21]_:

        .. math:: P_{wpp}=\frac{1}{8}\cdot\rho_{air,hub}\cdot d_{rotor}^{2}
            \cdot\pi\cdot v_{wind}^{3}\cdot cp\left(v_{wind}\right)

        with:
            v: wind speed [m/s], d: diameter [m], :math:`\rho`: density [kg/m³]

        ToDo: Check the equation and add references.

        References
        ----------
        .. [21] Gasch R., Twele J.: "Windkraftanlagen". 6. Auflage, Wiesbaden,
                Vieweg + Teubner, 2010, pages 35ff, 208

        See Also
        --------
        get_normalized_wind_pp_time_series
        """
        weather = kwargs['weather']
        p_wpp = (
            (self.rho_hub(weather) / 2) *
            (((self.powerplant.d_rotor / 2) ** 2) * np.pi) *
            np.power(self.v_wind_hub(weather), 3) *
            self.cp_values(self.v_wind_hub(weather), **kwargs))

        p_wpp_series = pd.Series(data=p_wpp,
                                 index=kwargs['weather'].data.index,
                                 name='feedin_wind_pp')

        return p_wpp_series.clip(
            upper=(float(self.nominal_power_wind_turbine)))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
