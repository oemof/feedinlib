# -*- coding: utf-8 -*-
"""
@author: oemof developing group

https://github.com/oemof
"""

import os
import sys
import numpy as np
import pandas as pd
import pvlib
import logging
try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve


class Photovoltaic:
    r"""Model to determine the output of a photovoltaik module

    The calculation is based on the library pvlib. [1]_

    Parameters
    ----------
    required : list of strings
        Containing the names of the required parameters to use the model.

    See Also
    --------
    WindPowerPlant

    Notes
    -----
    For more information about the photovoltaik model check the documentation
    of the pvlib library.

    https://readthedocs.org/projects/pvlib-python/

    References
    ----------
    .. [1] `pvlib on github <https://github.com/pvlib/pvlib-python>`_

    Examples
    --------
    >>> from feedinlib import models
    >>> required_ls = ['module_name', 'azimuth', 'tilt', 'albedo', 'tz']
    >>> required_ls += ['latitude', 'longitude']
    >>> pv_model = models.Photovoltaic(required=required_ls)

    """

    def __init__(self, required):
        self.required = required
        self.area = None
        self.peak = None

    def feedin(self, **kwargs):
        r"""
        Feedin time series for the given pv module.

        In contrast to :py:func:`turbine_power_output
        <feedinlib.models.Photovoltaic.get_pv_power_output>` it returns just
        the feedin series instead of the whole DataFrame.

        Parameters
        ----------
        see :
            :py:func:`turbine_power_output
            <feedinlib.models.Photovoltaic.get_pv_power_output>`

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
                                tz=kwargs['tz']))

        data_5min = pvlib.solarposition.get_solarposition(
            time=data_5min.index, location=location, method='ephemeris')

        return pd.concat(
            [data, data_5min.clip_lower(0).resample('H', how='mean')],
            axis=1, join='inner')

    def solarposition(location, data, **kwargs):
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

        See Also
        --------
        solarposition_hourly_mean : calculates the position of the sun as an
            hourly mean.

        Notes
        -----
        This method is not used in favour to solarposition_hourly_mean.
        """
        return pd.concat(
            [data, pvlib.solarposition.get_solarposition(
                time=data.index, location=location, method='ephemeris')],
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
            surface_tilt=kwargs['tilt'], surface_azimuth=kwargs['azimuth'])

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

        See Also
        --------
        solarposition_hourly_mean, solarposition, angle_of_incidenc

        References
        ----------
        .. [5] `pvlib globalinplane <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#pvlib.irradiance.globalinplane>`_.
        .. [6] `pvlib atmosphere <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#module-pvlib.atmosphere>`_.
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
            surface_tilt=kwargs['tilt'],
            surface_azimuth=kwargs['azimuth'],
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
            albedo=kwargs['albedo'],
            surface_tilt=kwargs['tilt'])

        # Determine total in-plane irradiance
        data = pd.concat(
            [data, pvlib.irradiance.globalinplane(
                aoi=data['aoi'],
                dni=data['dni'],
                poa_sky_diffuse=data['poa_sky_diffuse'],
                poa_ground_diffuse=data['poa_ground_diffuse'])],
            axis=1, join='inner')

        return data

    def fetch_module_data(self, **kwargs):
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

        See Also
        --------
        pv_module_output
        """
        basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
        filename = os.path.join(basic_path, 'sam-library-sandia-modules.csv')
        if not os.path.exists(basic_path):
            os.makedirs(basic_path)
        if not os.path.isfile(filename):
            url_file = 'sam-library-sandia-modules-2015-6-30.csv'
            url = 'https://sam.nrel.gov/sites/sam.nrel.gov/files/' + url_file
            urlretrieve(url, filename)
        module_data = (pvlib.pvsystem.retrieve_sam(samfile=filename)
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

        See Also
        --------
        global_in_plane_irradiation

        References
        ----------
        .. [8] `pvlib pv-system <http://pvlib-python.readthedocs.org/en/
                latest/pvlib.html#pvlib.pvsystem.sapm>`_.
        .. [9] `module library <https://sam.nrel.gov/sites/sam.nrel.gov/files/
                sam-library-sandia-modules-2015-6-30.csv>`_.
        .. [10] `pvlib get_solarposition <http://pvlib-python.readthedocs.org
                /en/latest/pvlib.html#pvlib.solarposition.get_solarposition>`_.
        """
        # Determine module and cell temperature
        data['temp_air_celsius'] = data['temp_air'] - 273.15
        data = pd.concat([data, pvlib.pvsystem.sapm_celltemp(
            irrad=data['poa_global'],
            wind=data['v_wind'],
            temp=data['temp_air_celsius'],
            model='Open_rack_cell_polymerback')], axis=1, join='inner')

        # Retrieve the module data object
        module_data = self.fetch_module_data(**kwargs)

        # Apply the Sandia PV Array Performance Model (SAPM) to get a
        data = pd.concat([data, pvlib.pvsystem.sapm(
            poa_direct=data['poa_direct'],
            poa_diffuse=data['poa_diffuse'],
            temp_cell=data['temp_cell'],
            airmass_absolute=data['airmass'],
            aoi=data['aoi'],
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
        latitude : float
            latitude of the irradiation data
        longitude: float
            longitude of the irradiation data
        tz : string
            timezone of the irradiation data e.g. Europe/Berlin
        data : pandas.DataFrame
            Containing the timeseries as columns (temp_air, v_wind, dhi,
            dirhi).
        weather : oemof.energy_weather object
            Containing a DataFrame with all needed data sets.
        modul_name : string
            name of a pv module from the sam.nrel database [12]_
        tilt : float
            tilt angle of the pv module (horizontal=0°)
        azimuth : float
            azimuth angle of the pv module (south=180°)
        albedo : float
            albedo factor arround the module
        Returns
        -------
        pandas.DataFrame
            The DataFrame contains the following new columns: p_pv_norm,
            p_pv_norm_area and all timeseries calculated before.

        See Also
        --------
        pv_module_output, feedin

        References
        ----------
        .. [11] `pvlib documentation <https://readthedocs.org/projects/
                pvlib-python/>`_.
        .. [12] `module library <https://sam.nrel.gov/sites/sam.nrel.gov/files/
                sam-library-sandia-modules-2015-6-30.csv>`_.
        """
        # If no DataFrame is given, try to get the data from a weather object
        if kwargs.get('data', None) is None:
            data = kwargs['weather'].get_feedin_data(
                gid=kwargs.get('gid', None))
        else:
            data = kwargs.pop('data')

        # Create a location object
        location = pvlib.location.Location(kwargs['latitude'],
                                           kwargs['longitude'],
                                           kwargs['tz'])

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


class WindPowerPlant:
    r"""Model to determine the output of a wind turbine

    Parameters
    ----------
    required : list of strings
        Containing the names of the required parameters to use the model.

    Examples
    --------
    >>> from feedinlib import models
    >>> required_ls = ['h_hub', 'd_rotor', 'wind_conv_type', 'data_height']
    >>> wind_model = models.WindPowerPlant(required=required_ls)

    See Also
    --------
    Photovoltaic
    """

    def __init__(self, required):
        self.required = required
        self.nominal_power_wind_turbine = None

    def feedin(self, **kwargs):
        r"""
        Alias for :py:func:`turbine_power_output
        <feedinlib.models.WindPowerPlant.turbine_power_output>`.
        """
        return self.turbine_power_output(**kwargs)

    def get_wind_pp_types(self, conn=None, print_out=True):
        r"""
        Get the names of all possible wind converter types.

        Parameters
        ----------
        data : sqlalchemy connection object, optional
            A valid connection object to a database.

        Examples
        --------
        >>> from feedinlib import models
        >>> w_model = models.WindPowerPlant(required=[])
        >>> valid_types_df = w_model.get_wind_pp_types(print_out=False)
        >>> valid_types_df.shape
        (91, 2)
        """
        if conn is None:
            res_df, df = self.fetch_cp_values_from_file(wind_conv_type='')
        else:
            res_df, df = self.fetch_cp_values_from_db(wind_conv_type='')
        if print_out:
            pd.set_option('display.max_rows', len(df))
            print(df[['rli_anlagen_id', 'p_nenn']])
            pd.reset_option('display.max_rows')
        return df[['rli_anlagen_id', 'p_nenn']]

    def fetch_data_heights_from_weather_object(self, **kwargs):
        ''
        dic = {}
        for key in kwargs['data'].keys():
            dic[key] = kwargs['weather'].get_data_heigth(key)
            if dic[key] is None:
                dic[key] = 0
        return dic

    def rho_hub(self, **kwargs):
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

        The following equations are used:

        .. math:: T_{hub}=T_{air, data}-0.0065\cdot\left(h_{hub}-h_{T,data}
            \right)
        .. math:: p_{hub}=\left(p_{data}/100-\left(h_{hub}-h_{p,data}\right)
            *\frac{1}{8}\right)/\left(2.8706\cdot T_{hub}\right)

        with T: temperature [K], h: height [m], p: pressure [Pa]

        ToDo: Check the equation and add references.

        References
        ----------
        Missing references.

        See Also
        --------
        v_wind_hub
        """
        h_temperature_data = kwargs['data_height']['temp_air']
        h_pressure_data = kwargs['data_height']['pressure']
        T_hub = kwargs['data'].temp_air - 0.0065 * (
            kwargs['h_hub'] - h_temperature_data)
        return (
            kwargs['data'].pressure / 100 -
            (kwargs['h_hub'] - h_pressure_data) * 1 / 8) / (2.8706 * T_hub)

    def v_wind_hub(self, **kwargs):
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
        The following equation is used:

        .. math:: v_{wind,hub}=v_{wind,data}\cdot\frac{\ln\left(\frac{h_{hub}}
            {z_{0}}\right)}{\ln\left(\frac{h_{data}}{z_{0}}\right)}


        with:
            v: wind speed [m/s], h: height [m], z0: roughnes length [m]

        :math:`h_{data}` is the hight in which the wind velocity is measured.
        (height in m, velocity in m/s)

        ToDo: Check the equation and add references.

        References
        ----------
          *  Missing references.

        See Also
        --------
        rho_hub
        """
        return (kwargs['data'].v_wind * np.log(kwargs['h_hub'] /
                kwargs['data'].z0)
                / np.log(kwargs['data_height']['v_wind'] / kwargs['data'].z0))

    def fetch_cp_values_from_file(self, **kwargs):
        r"""
        Fetch cp values from a file or download it from a server.

        The files are located in the ~/.oemof folder.

        Parameters
        ----------
        wind_conv_type : string
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.

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
        basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
        filename = os.path.join(basic_path, 'cp_values')
        url = 'http://vernetzen.uni-flensburg.de/~git/cp_values'
        suffix = '.hf5'
        if not os.path.exists(basic_path):
            os.makedirs(basic_path)
        if not os.path.isfile(filename + suffix):
            urlretrieve(url + suffix, filename + suffix)
            logging.info('Copying cp_values from {0} to {1}'.format(
                url, filename + suffix))
        logging.debug('Retrieving cp values from {0}'.format(
            filename + suffix))
        try:
            df = pd.read_hdf(filename + suffix, 'cp')
        except:
            suffix = '.csv'
            logging.info('Failed loading cp values from hdf file, trying csv.')
            logging.debug('Retrieving cp values from {0}'.format(
                filename + suffix))
            if not os.path.isfile(filename + suffix):
                urlretrieve(url + suffix, filename + suffix)
                logging.info('Copying cp_values from {0} to {1}'.format(
                    url, filename + suffix))
            df = pd.read_csv(filename + suffix, index_col=0)
        res_df = df[df.rli_anlagen_id == kwargs[
            'wind_conv_type']].reset_index(drop=True)
        return res_df, df

    def fetch_cp_values_from_db(self, **kwargs):
        r"""
        Fetch cp values from a the oemof postgresql database.

        The table is named "wea_cpcurves" and is located in the oemof_test
        schema of the oemof database.

        Parameters
        ----------
        wind_conv_type : string
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.

        Returns
        -------
        pandas.DataFrame
            cp values, wind converter type, installed capacity or the full
            table if the given wind converter cannot be found in the table.

        See Also
        --------
        fetch_cp_values_from_file
        """
        # TODO@Günni
        sql = '''SELECT * FROM oemof_test.
            WHERE rli_anlagen_id = '{0}';
            '''.format(kwargs['wind_conv_type'])
        logging.info('Retrieving cp values from {0}'.format(
            'postgresql database'))
        db_res = kwargs['connection'].execute(sql)
        res_df = pd.DataFrame(db_res.fetchall(), columns=db_res.keys())
        if res_df.shape[0] == 0:
            sql = 'SELECT * FROM oemof_test.wea_cpcurves;'
            db_res = kwargs['connection'].execute(sql)
            db_res = kwargs['connection'].execute(sql)
            df = pd.DataFrame(db_res.fetchall(), columns=db_res.keys())
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


        >>> from feedinlib import models
        >>> w_model = models.WindPowerPlant(required=['wind_conv_type'])
        >>> cp = w_model.fetch_cp_values(wind_conv_type='ENERCON E 126 7500')
        >>> print(cp.loc[0, :][2:55].sum())
        6.495

        See Also
        --------
        fetch_cp_values_from_db, fetch_cp_values_from_file
        """
        if kwargs.get('cp_values', None) is not None:
            res_df = kwargs.get['cp_values']
        elif kwargs.get('connection', None) is None:
            res_df, df = self.fetch_cp_values_from_file(**kwargs)
        else:
            res_df, df = self.fetch_cp_values_from_db(**kwargs)
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
        >>> w = models.WindPowerPlant(required=['wind_conv_type', 'v_wind'])
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
        self.nominal_power_wind_turbine = res_df['p_nenn'][0]
        v_wind[v_wind > np.max(cp_data[:, 0])] = np.max(cp_data[:, 0])
        return np.interp(v_wind, cp_data[:, 0], cp_data[:, 1])

    def turbine_power_output(self, **kwargs):
        r"""
        Calculates the power output in W of one wind turbine.

        Parameters
        ----------
        data : DataFrame
            Containing columns with the timeseries for wind speed (v_wind),
            roughness length (z0), temperature (temp_air) and pressure
            (pressure).
        data_height : DataFrame or Dictionary
            Containing columns or keys with the height of the measurement or
            model data for temperature (temp_air) and wind speed (v_wind).
        h_hub : float
            Height of the hub of the wind turbine
        d_rotor: float
            'Diameter of the rotor [m]',
        wind_conv_type : string
            Name of the wind converter type. Use self.get_wind_pp_types() to
            see a list of all possible wind converters.

        Returns
        -------
        pandas.Series
            Electrical power of the wind turbine

        Notes
        -----
        The following equation is used:

        .. math:: P_{wpp}=\frac{1}{8}\cdot\rho_{air,hub}\cdot d_{rotor}^{2}
            \cdot\pi\cdot v_{wind}^{3}\cdot cp\left(v_{wind}\right)

        with:
            v: wind speed [m/s], d: diameter [m], :math:`\rho`: density [kg/m³]

        ToDo: Check the equation and add references.

        References
        ----------
          *  Missing references.

        See Also
        --------
        get_normalized_wind_pp_time_series
        """
        # If weather object is given, use it.
        if kwargs.get('weather', None) is not None:
            kwargs['data'] = kwargs['weather'].get_feedin_data(
                gid=kwargs.get('gid', None))
            kwargs['data_height'] = (
                self.fetch_data_heights_from_weather_object(**kwargs))

        kwargs['data'].p_wpp = (
            (self.rho_hub(**kwargs) / 2) *
            (((kwargs['d_rotor'] / 2) ** 2) * np.pi) *
            np.power(self.v_wind_hub(**kwargs), 3) *
            self.cp_values(self.v_wind_hub(**kwargs), **kwargs))
        return kwargs['data'].p_wpp.clip(
            upper=(float(self.nominal_power_wind_turbine * 10 ** 3)))


class ConstantModell:
    ''
    def __init__(self, required=["nominal_power", "steps"]):
        self.required = required

    def feedin(self, **ks):
        return [ks["nominal_power"]*0.9] * ks["steps"]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
