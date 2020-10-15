# -*- coding: utf-8 -*-

"""
Geometric solar feed-in model class.

SPDX-FileCopyrightText: Lucas Schmeling
SPDX-FileCopyrightText: Keno Oltmanns
SPDX-FileCopyrightText: Patrik Schönfeldt <patrik.schoenfeldt@dlr.de>

SPDX-License-Identifier: MIT

This module holds implementations of solar feed-in models based on geometry.
I.e. it calculates the angles solar radiation hits a collector.

=========================== ======================= =========
symbol                      explanation             attribute
=========================== ======================= =========
:math:`t`                   time (absolute,         :py:obj:`datetime`
                            including date)
:math:`\beta`               slope of collector      :py:obj:`tilt`
:math:`\gamma`              direction, the          :py:obj:`surface_azimuth`
                            collector faces
:math:`\phi`                location (N-S)          :py:obj:`longitude`
:math:`L_{loc}`             location (O-W)          :py:obj:`latitude`


[DB13] Duffie, John A.; Beckman, William A.:
    Solar Engineering of Thermal Processes (2013),
    DOI: 10.1002/9781118671603

"""

import numpy as np

SOLAR_CONSTANT = 1367  # in W/m²


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
                       - longitude / 3)
    hour_angle = np.deg2rad(15 * (true_solar_time - 12.0))
    solar_declination_angle = np.deg2rad(23.45) * np.sin(
        2 * np.pi / 365 * (284 + day_of_year))

    # DB13, Eq. 1.6.5
    solar_zenith_angle = (
            np.sin(solar_declination_angle) * np.sin(latitude)
            + np.cos(solar_declination_angle) * np.cos(latitude)
            * np.cos(hour_angle))

    # DB13, Eq. 1.6.2
    angle_of_incidence = (
            + np.sin(solar_declination_angle) * np.sin(latitude)
            * np.cos(tilt)
            - np.sin(solar_declination_angle) * np.cos(latitude)
            * np.sin(tilt) * np.cos(surface_azimuth)
            + np.cos(solar_declination_angle) * np.cos(latitude)
            * np.cos(tilt) * np.cos(hour_angle)
            + np.cos(solar_declination_angle) * np.sin(latitude)
            * np.sin(tilt) * np.cos(surface_azimuth) * np.cos(hour_angle)
            + np.cos(solar_declination_angle) * np.sin(tilt)
            * np.sin(surface_azimuth) * np.sin(hour_angle))

    # We do not allow backside illumination.
    angle_of_incidence = np.array(angle_of_incidence)
    angle_of_incidence[angle_of_incidence < 0] = 0

    solar_zenith_angle = np.array(solar_zenith_angle)

    return angle_of_incidence, solar_zenith_angle


def geometric_radiation(data_weather,
                        collector_slope, surface_azimuth,
                        longitude, latitude,
                        albedo=0.2):
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
    albedo : numeric (default: 0.2)
        ground reflectance of sourounding area

    Returns
    -------
    :pandas:`pandas.DataFrame<dataframe>`
    containing the total radiation on the sloped surface
    """

    angle_of_incidence, solar_zenith_angle = solar_angles(
        data_weather.index, collector_slope, surface_azimuth,
        longitude, latitude)

    sunset_angle = 6  # degree
    angle_of_incidence[solar_zenith_angle < np.cos(
        np.deg2rad(90 - sunset_angle))] = 0

    # beam radiation correction factor
    beam_correction_factor = np.array(angle_of_incidence
                                      / solar_zenith_angle)

    dni = data_weather['dni']
    dhi = data_weather['dhi']

    irradiation = dni + dhi

    # direct radiation
    radiation_directed = dni * beam_correction_factor

    print(radiation_directed)

    # DIFFUSE RADIATION
    # horizon brightening diffuse correction term
    f = np.sqrt(dni / irradiation).fillna(0)
    # Anisotropy index
    anisotropy_index = dni / SOLAR_CONSTANT

    collector_slope = np.deg2rad(collector_slope)
    diffuse_radiation_correction_factor = (1 - anisotropy_index) * (
            (1 + np.cos(collector_slope)) / 2) * (1 + f * np.sin(
                collector_slope / 2) ** 3) + (anisotropy_index
                                              * beam_correction_factor)

    # diffuse radiation
    radiation_diffuse = dhi * diffuse_radiation_correction_factor

    radiation_reflected = (1 - np.cos(collector_slope)) * albedo / 2
    radiation_reflected = irradiation * radiation_reflected

    # Total radiation
    return radiation_directed + radiation_diffuse + radiation_reflected


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
            direction, collector surface faces (in Degree)
            (e.g. Equathor: 0, East: -180, West: +180)
        longitude : numeric
            location (east–west) of solar plant installation
        latitude : numeric
            location (north-south) of solar plant installation
        albedo : numeric, default 0.2
        nominal_peak_power : numeric, default : 1
            nominal peak power of the installation
        radiation_STC : numeric, default: 1000
            Radiation (in W/m²) under standard test condition
        temperature_STC : numeric, default: 25
            Temperature (in °C) under standard test condition
        temperature_NCO : numeric, default: 45
            Normal operation cell temperature (in °C)
        temperature_coefficient: numeric, default: 0.004
        system_efficiency : numeric, default: 0.8
            overall system efficiency (inverter, etc.)
        """

        self.tilt = attributes.get("tilt")
        self.azimuth = attributes.get("azimuth")
        self.longitude = attributes.get("longitude")
        self.latitude = attributes.get("latitude")
        self.albedo = attributes.get("albedo", 0.2)
        self.nominal_peak_power = attributes.get("nominal_peak_power", 1)

        self.radiation_STC = attributes.get("radiation_STC", 1000)
        self.temperature_STC = attributes.get("temperature_STC", 25)
        self.temperature_NCO = attributes.get("temperature_NCO", 45)
        self.temperature_coefficient = attributes.get(
            "temperature_coefficient", 0.004)
        self.system_efficiency = attributes.get("system_efficiency", 0.80)

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

        radiation_surface = geometric_radiation(weather,
                                                self.tilt,
                                                self.azimuth,
                                                self.longitude,
                                                self.latitude)

        temperature_cell = weather['temp_air'] + radiation_surface/800 * (
                (self.temperature_NCO - 20))

        feedin = (self.nominal_peak_power * radiation_surface /
                  self.radiation_STC * (1 - self.temperature_coefficient * (
                        temperature_cell - self.temperature_STC)))

        feedin[feedin < 0] = 0

        return feedin * self.system_efficiency

    def solar_angles(self, datetime):
        return solar_angles(datetime,
                            self.tilt, self.azimuth,
                            self.longitude, self.latitude)

