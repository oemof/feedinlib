# -*- coding: utf-8 -*-

"""
Geometric solar feed-in model class.

SPDX-FileCopyrightText: Lucas Schmeling
SPDX-FileCopyrightText: Keno Oltmanns
SPDX-FileCopyrightText: Patrik Schönfeldt <patrik.schoenfeldt@dlr.de>

SPDX-License-Identifier: MIT

This module holds implementations of solar feed-in models based on geometry.
I.e. it calculates the angles solar radiation hits a collector.
"""

import numpy as np


class GeometricSolar:
    r"""
    Model to determine the feed-in of a solar plant using geometric formulas.
    """

    def __init__(self, **attributes):
        """
        Parameters
        ----------
        tilt : numeric
            collector tilt in degree
        azimuth : numeric
            collector surface azimuth in degree
        longitude : numeric
            location (east–west) of solar plant installation
        latitude : numeric
            location (north-south) of solar plant installation
        peak_power : numeric, default : 1
            nominal peak power of the installation
        """

        self.tilt = attributes.get("tilt")
        self.azimuth = attributes.get("azimuth")
        self.longitude = attributes.get("longitude")
        self.latitude = attributes.get("latitude")
        self.pv_system_peak_power = attributes.get("peak_power", 1)

        self.PV_ISTC = 1000  # Radiation under standard test condition
        self.PV_TSTC = 25  # Temperature under standard test condition
        self.PV_NOCT = 45  # Normal operation cell temperature
        self.PV_TEMP_COEFFICIENT = 0.004  # Temperature coefficient
        self.PV_LOSS = 0.20  # Percental loss due to lines, inverter, dirt etc.

    def feedin(self, weather):
        """
        Parameters
        ----------
        weather : :pandas:`pandas.DataFrame<dataframe>`
            containing direct radiation ('dni') and diffuse radiation ('dhi')

        Returns
        -------
        :pandas:`pandas.Series<series>`
            Series with PV system feed-in in the unit the peak power was given.

        """

        radiation_surface = GeometricSolar.geometric_radiation(weather,
                                                               self.tilt,
                                                               self.azimuth,
                                                               self.longitude,
                                                               self.latitude)

        temperature_cell = weather['temp_air'] + radiation_surface * (
                (self.PV_NOCT - 20) / 800)

        feedin = (self.pv_system_peak_power * radiation_surface /
                self.PV_ISTC * (1 - self.PV_TEMP_COEFFICIENT * (
                        temperature_cell - self.PV_TSTC)))

        feedin[feedin < 0] = 0

        return feedin * (1 - self.PV_LOSS)

    @staticmethod
    def solar_angles(datetime,
                     tilt, surface_azimuth,
                     longitude, latitude):
        """
        Calculate the radiation on a sloped surface

        Parameters
        ----------
        datetime : :pandas:`pandas.DatetimeIndex<datetimeindex>`
            points in time to calculate radiation for
            (need to be time zone aware)
        tilt : numeric
            collector tilt in degree
        surface_azimuth : numeric
            collector surface azimuth in degree
        longitude : numeric
            location (east–west) of solar plant installation
        latitude : numeric
            location (north–south) of solar plant installation

        Returns
        -------
        two numpy arrays
            containing the cosine of angle of incidence,
            and of the solar zenith angle, respectively.


        [DB13] Duffie, John A.; Beckman, William A.:
            Solar Engineering of Thermal Processes (2013),
            DOI: 10.1002/9781118671603
        """

        tilt = np.deg2rad(tilt)
        latitude = np.deg2rad(latitude)

        # convert time zone (to UTC)
        datetime = datetime.tz_convert(tz='UTC')

        day_of_year = datetime.dayofyear
        # DB13, Eq. 1.4.2 but using angles in Rad.
        day_angle = 2 * np.pi * (day_of_year - 1) / 365

        # DB13, Eq. 1.5.3
        equation_of_time = 229.2 * (0.000075
                                    + 0.001868 * np.cos(day_angle)
                                    - 0.030277 * np.sin(day_angle)
                                    - 0.014615 * np.cos(2 * day_angle)
                                    - 0.04089 * np.sin(2 * day_angle))

        true_solar_time = (datetime.hour + (datetime.minute
                                            + equation_of_time) / 60
                           - longitude/3)
        hour_angle = np.deg2rad(15 * (true_solar_time - 12.0))
        solar_declination_angle = np.deg2rad(23.45) * np.sin(2 * np.pi / 365 * (284 + day_of_year))

        # DB13, Eq. 1.6.5
        solar_zenith_angle = (
                np.sin(solar_declination_angle) * np.sin(latitude)
                + np.cos(solar_declination_angle) * np.cos(latitude) * np.cos(hour_angle))

        # DB13, Eq. 1.6.2
        angle_of_incidence = (
                + np.sin(solar_declination_angle) * np.sin(latitude) * np.cos(tilt)
                - np.sin(solar_declination_angle) * np.cos(latitude) * np.sin(tilt) * np.cos(
                surface_azimuth)
                + np.cos(solar_declination_angle) * np.cos(latitude) * np.cos(tilt) * np.cos(hour_angle)
                + np.cos(solar_declination_angle) * np.sin(latitude) * np.sin(tilt)
                * np.cos(surface_azimuth) * np.cos(hour_angle)
                + np.cos(solar_declination_angle) * np.sin(tilt) * np.sin(surface_azimuth)
                * np.sin(hour_angle))

        # We do not allow backside illumination.
        angle_of_incidence = np.array(angle_of_incidence)
        angle_of_incidence[angle_of_incidence < 0] = 0

        solar_zenith_angle = np.array(solar_zenith_angle)

        return angle_of_incidence, solar_zenith_angle

    @staticmethod
    def geometric_radiation(data_weather,
                            collector_slope, surface_azimuth,
                            longitude, latitude):
        """
        Refines the simplistic clear sky model by taking weather conditions
        and losses of the PV installation into account

        Parameters
        ----------
        data_weather : :pandas:`pandas.DataFrame<dataframe>`
        collector_slope : numeric
            collector tilt in degree
        surface_azimuth : numeric
            collector surface azimuth in degree
        longitude : numeric
            location (east–west) of solar plant installation
        latitude : numeric
            location (north–south) of solar plant installation

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`
        containing the total radiation on the sloped surface
        """

        # load 'simplistic_clear_sky' irradiation
        angle_of_incidence, solar_zenith_angle = GeometricSolar.solar_angles(
            data_weather.index, collector_slope, surface_azimuth,
            longitude, latitude)

        # Solar constant
        SOLAR_CONSTANT = 1367

        # ground reflectance (albedo) of grass
        albedo_RHO = 0.2

        sunset_angle = 6  # degree
        solar_zenith_angle[solar_zenith_angle < np.cos(np.deg2rad(90 - sunset_angle))] = 1

        # beam radiation correction factor
        beam_correction_factor = np.array(angle_of_incidence / solar_zenith_angle)

        dni = data_weather['dni']
        dhi = data_weather['dhi']

        irradiation = dni + dhi

        # direct radiation
        radiation_directed = dni * beam_correction_factor

        # DIFFUSE RADIATION
        # horizon brightening diffuse correction term
        f = np.sqrt(dni / irradiation).fillna(0)
        # Anisotropy index
        anisotropy_index = dni / SOLAR_CONSTANT

        collector_slope = np.deg2rad(collector_slope)
        diffuse_radiation_correction_factor = (1 - anisotropy_index) * ((1 + np.cos(collector_slope)) / 2) \
                                     * (1 + f * np.sin(
            collector_slope / 2) ** 3) + anisotropy_index * beam_correction_factor

        # diffuse radiation
        radiation_diffuse = dhi * diffuse_radiation_correction_factor

        radiation_reflected = (1 - np.cos(collector_slope)) * albedo_RHO / 2
        radiation_reflected = irradiation * radiation_reflected

        # Total radiation
        return radiation_directed + radiation_diffuse + radiation_reflected