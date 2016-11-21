# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 12:41:37 2015

@author: uwe
"""

import nose.tools as nt
import os.path
import pandas
import numpy

from feedinlib import models as model
from feedinlib import powerplants as plant
from feedinlib import weather


class ModelsPowerplantsInteraction_Tests:

    @classmethod
    def setUpClass(self):
        self.required_parameter = {}
        self.required_parameter['wind_model'] = {
            'h_hub': 'height of the hub in meters',
            'd_rotor': 'diameter of the rotor in meters',
            'wind_conv_type':
            'wind converter according to the list in the csv file.'}

        self.required_parameter['pv_model'] = {
            'azimuth': 'Azimuth angle of the pv module',
            'tilt': 'Tilt angle of the pv module',
            'module_name': 'According to the sandia module library.',
            'albedo': 'Albedo value'}

        self.height_of_measurement = {
            'dhi': 0,
            'dirhi': 0,
            'pressure': 0,
            'temp_air': 2,
            'v_wind': 10,
            'Z0': 0}

        self.site = {
            'module_name': 'Yingli_YL210__2008__E__',
            'azimuth': 180,
            'tilt': 30,
            'albedo': 0.2,
            'h_hub': 135,
            'd_rotor': 127,
            'wind_conv_type': 'ENERCON E 126 7500'}

        timezone = 'Europe/Berlin'
        n = 876
        self.weather_df = pandas.DataFrame(index=pandas.date_range(
            pandas.datetime(2010, 1, 1, 0), periods=n, freq='H',
            tz=timezone))
        self.weather_df['temp_air'] = 280.5 * numpy.ones(n)
        self.weather_df['pressure'] = 100168 * numpy.ones(n)
        self.weather_df['dirhi'] = 111 * numpy.ones(n)
        self.weather_df['dhi'] = 111 * numpy.ones(n)
        self.weather_df['v_wind'] = 4.8 * numpy.ones(n)
        self.weather_df['z0'] = 0.15 * numpy.ones(n)
        self.weather = weather.FeedinWeather(
            data=self.weather_df,
            timezone=timezone,
            latitude=52,
            longitude=12,
            data_height=self.height_of_measurement)

    @nt.raises(AttributeError)
    def test_pv_model(self):
        plant.Photovoltaic(model=model.PvlibBased(required=["missing"]))

    @nt.raises(AttributeError)
    def test_wind_model(self):
        plant.WindPowerPlant(model=model.SimplewindTurbine(["missing"]))

    @nt.raises(FileNotFoundError)
    def test_csv_weather_file(self):
        my_weather = weather.FeedinWeather()
        my_weather.read_feedinlib_csv(filename='')

    def type_dataframe_test(self):
        nt.ok_(isinstance(self.weather.data,
                          pandas.core.frame.DataFrame))

    def test_load_feedinlib(self):
        my_weather = weather.FeedinWeather()
        basic_path = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(basic_path, 'test_weather.csv')
        my_weather.read_feedinlib_csv(filename=filename)

    def wind_result_test(self):
        wind_model = model.SimpleWindTurbine(
            required=list(self.required_parameter['wind_model'].keys()))
        wind_power_plant = plant.WindPowerPlant(model=wind_model, **self.site)
        wka_feedin = wind_power_plant.feedin(weather=self.weather)
        nt.eq_(round(wka_feedin.sum() / 1000), 1523340.0)

    def pv_result_test(self):
        pv_model = model.PvlibBased(
            required=list(self.required_parameter['pv_model'].keys()))
        pv_plant = plant.Photovoltaic(model=pv_model, **self.site)
        pv_feedin = pv_plant.feedin(weather=self.weather)
        nt.eq_(round(pv_feedin.sum() / 1000), 31.0)
