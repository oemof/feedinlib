#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 17:10:54 2015

@author: guido

"""

from feedinlib import powerplants as plants
from feedinlib import models
from feedinlib import weather
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
import logging
import os
import pandas as pd
try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve


def pv_generation_reference_data():
    '''returns a dict containing reference data at different locations'''
    reference_data = {
        'pv_biesdorf': { # runs with CEC
#            'module_name': 'Sovello_SV_X_205_yyy', #original module
            'module_name': 'SunPower_SPR_205_BLK__2007__E__',
            'capacity': 7640,
            'azimuth': None,
            'tilt': None,
            'inverter': 'Sunny Boy 3300', #currently not used
            'generation': {
                '2012': 7260.42,
                '2013': 6464.78,                
                '2014': 7023.52
                },
            'location': {
                'lat': 52.499622,
                'lon': 13.527300
                },
            'tz': 'Europe/Berlin',
            'source': { #currently not used
                'url': '''https://www.sunnyportal.com/Templates/PublicPageOver
                    view.aspx?page=dfdf49a9-b839-4d05-bd92-fb68931e567d&plant=
                    937abc59-1292-456a-a2b2-a09cfb25fc06&splang=de-DE''',
                'city': 'berlin',
                'district': 'biesdorf'
                }
            },
        'kz_gedenkstaette_neckarelz': { # runs with CEC
#            'module_name': 'SolarWorld_SW240_Poly', #original module
            'module_name': 'Suniva_Titan_240__2009__E__',
            'capacity': 16.32,
            'azimuth': 0,
            'tilt': 7,
            'inverter': 'SMA STP 15000 TL-10', #currently not used
            'generation': {
                '2013': 13598.494,                
                '2014': 13271.848
                },
            'location': {
                'lat': 49.341495,
                'lon': 9.110596
                },
            'tz': 'Europe/Berlin',
            'source': { #currently not used
                'url': '''http://www.suntrol-portal.com/de/page/
                    kz-gedenkstaette-neckarelz''',
                'city': 'Mosbach',
                'street': 'Mosbacher Str. 39'
                }
            }
        }
    return reference_data
    
    
def wind_generation_reference_data():
    '''returns a dict containing reference data at different locations'''
    reference_data = {
        'brandenkopf': {
            'wind_conv_type': 'ENERCON E 58 1000',
            'number': 1,
            'h_hub': 70.5, #135, # estimated by 
            #http://en.wind-turbine-models.com/turbines/114-enercon-e-58-10.58
            'd_rotor': 58, #127, #58,
            'generation': {
                '2003': 2069520 / 1e3,
                '2007': 2373958 / 1e3,
                '2010': 1781191 / 1e3,             
                '2011': 1918396 / 1e3,
                '2012': 2046413 / 1e3,
                '2013': 2028387 / 1e3,
                },
            'location': {
                'lat': 48.339559,
                'lon': 8.154681
                },
            'tz': 'Europe/Berlin',
            'source': { #currently not used
                'url': '''http://www.buergerwindrad-brandenkopf.de'''
                },
            'comment': '''Der Brandenkopf mit 945 m Höhe ist innerhalb 
                Baden-Württembergs in seiner Gipfellage der zweitbeste 
                Windkraftstandort in den Statistiken des Landes. Die mittlere 
                Jahreswindgeschwindigkeit auf dem Brandenkopf beträgt 
                ca. 5,8 m/s. Auf dem Brandenkopf befindet sich das Wanderheim 
                des Schwarzwaldvereins, ein Aussichtsturm und eine Anlage der 
                Deutschen Telekom.'''
            },
        'hilchenbach': {
            'wind_conv_type': 'ENERCON E 82 2000',
            'number': 5,
            'h_hub': 138,
            'd_rotor': 82,
            'generation': {
                '2010': 18267382 / 1e3,             
                '2011': 20113852 / 1e3,
                '2012': 20113852 / 1e3,
                '2013': 20113852 / 1e3,
                '2014': 20372896 / 1e3
                },
            'location': {
                'lat': 51.016697,
                'lon': 8.1323475
                },
            'tz': 'Europe/Berlin',
            'source': { #currently not used
                'url': '''http://www.rothaarwind.de/windenergie/
                    mod_content_page/seite/Windstromertraege/index.html'''
                },
            'comment': 'average value of 5 power plants'
            }
        }
    return reference_data
    
    
def download_file(file, url, basic_path):
    filename = os.path.join(basic_path, file)
    if not os.path.isfile(filename):
        logging.info('Copying weather data from {0} to {1}'.format(
            url, filename))
        urlretrieve(os.path.join(url, file), filename)
    
    
def fetch_test_data_file(filename, basic_path):
    url = 'http://vernetzen.uni-flensburg.de/~git/'
    if not os.path.exists(basic_path):
        os.makedirs(basic_path)
    download_file(filename, url, basic_path)


def read_test_data(filename, datetime_column='Unnamed: 0'):
    df = pd.read_csv(filename)
    return df.set_index(pd.to_datetime(df[datetime_column])).tz_localize(
        'UTC').tz_convert('Europe/Berlin').drop(datetime_column, 1)


def pv_apply_feedinlib(coastDat_years, reference_data=None):

    # get reference data
    if reference_data is None:
        reference_data = pv_generation_reference_data()

    coastDat2 = {
        'dhi': 0,
        'dirhi': 0,
        'pressure': 0,
        'temp_air': 2,
        'v_wind': 10,
        'Z0': 0}
    pv_feedin_annual = {}
    basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
    
    # iterate over passed reference data dict
    for unit in list(reference_data.keys()):
        pv_feedin_annual[unit] = {}
        # update reference data with default values if values are missing
        if reference_data[unit]['azimuth'] is None:
            logging.warning('Azimuth unknown... overwrite with 0')
            reference_data[unit]['azimuth'] = 180
        if reference_data[unit]['tilt'] is None:
            logging.warning('Tilt unknown... overwrite with 30')
            reference_data[unit]['tilt'] = 30            
    
        years = [int(y) for y in reference_data[unit]['generation']]
        
        # choose module type and add location
        module_type = {'module_name': reference_data[unit]['module_name'],
                       'azimuth': reference_data[unit]['azimuth'],
                        'tilt': reference_data[unit]['tilt'],
                        'albedo': 0.2,
                        'latitude': reference_data[unit]['location']['lat'],
                        'longitude': reference_data[unit]['location']['lon'],
                        'tz': reference_data[unit]['tz']}
        pv_module = plants.Photovoltaic(model=models.PvlibBased, **module_type)

        for year in set(years).intersection(coastDat_years):
            # get weather data
            file =  'weather_' + unit + '_' + str(year) + '.csv'
            filename = os.path.join(basic_path, file)

            if not os.path.isfile(filename):
                fetch_test_data_file(file, basic_path)
            my_weather_df = read_test_data(filename)

            my_weather = weather.FeedinWeather(
                data=my_weather_df,
                timezone=reference_data[unit]['tz'],
                latitude=reference_data[unit]['location']['lon'],
                longitude=reference_data[unit]['location']['lat'],
                data_height=coastDat2)
                
            if reference_data[unit].get('module_number') is not None:
                pv_feedin_annual[unit][year] = pv_module.feedin(
                    weather=my_weather, 
                    number=reference_data[unit]['module_number']).sum() / 1e3
            elif reference_data[unit].get('capacity') is not None:
                pv_feedin_annual[unit][year] = pv_module.feedin(weather=
                    my_weather, peak_power=reference_data[unit]
                    ['capacity']).sum() / 1e3
            else:
                print('at least supply `module_number` or `capacity`')
    return pv_feedin_annual
    
    
def wind_apply_feedinlib(coastDat_years, reference_data):
    coastDat2 = {
        'dhi': 0,
        'dirhi': 0,
        'pressure': 0,
        'temp_air': 2,
        'v_wind': 10,
        'Z0': 0}
    basic_path = os.path.join(os.path.expanduser("~"), '.oemof')
        
    # iterate over passed reference data dict
    wind_feedin_annual = {}
    for unit in list(reference_data.keys()):
        wind_feedin_annual[unit] = {} 
    
        years = [int(y) for y in reference_data[unit]['generation']]

        wind_model = plants.WindPowerPlant(model=models.SimpleWindTurbine, **{
            'h_hub': reference_data[unit]['h_hub'],
            'd_rotor': reference_data[unit]['d_rotor'],
            'wind_conv_type': reference_data[unit]['wind_conv_type'],
            'data_height': coastDat2})

        for year in set(years).intersection(coastDat_years):
            # get weather data
            file =  'weather_' + unit + '_' + str(year) + '.csv'
            filename = os.path.join(basic_path, file)
            if not os.path.isfile(filename):
                fetch_test_data_file(file, basic_path)
            my_weather_df = read_test_data(filename)
            my_weather = weather.FeedinWeather(
                data=my_weather_df,
                timezone=reference_data[unit]['tz'],
                latitude=reference_data[unit]['location']['lon'],
                longitude=reference_data[unit]['location']['lat'],
                data_height=coastDat2)
            
            if reference_data[unit].get('number') is not None:
                wind_feedin_annual[unit][year] = wind_model.feedin(
                    weather=my_weather, 
                    number=reference_data[unit]['number']).sum() / 1e6
            elif reference_data[unit].get('capacity') is not None:
                wind_feedin_annual[unit][year] = wind_model.feedin(
                    weather=my_weather, installed_capacity=
                    reference_data[unit]['capacity']).sum()/1e6
            else:
                print('at least provide `number` or `capacity`')
    return wind_feedin_annual


def simple_plot(feedin, reference_data, coastDat_years):
    '''Make simple plots comparing model data with measured data'''
    for unit in list(feedin.keys()):
        reference_data_years = [int(x) for x in list(
                reference_data[unit]['generation'].keys())],
        for year in coastDat_years:
            if ((year in reference_data_years[0]) and (year in list(feedin
                [unit].keys()))):
                fig = plt.figure()
                ax = plt.subplot(111)
                ax.bar([0, 1], [feedin[unit][year], reference_data[unit]
                    ['generation'][str(year)]])
                if 'h_hub' in reference_data[unit]:
                    plt.ylabel('MWh per a')
                else:
                    plt.ylabel('kWh per a')
                plt.title(unit + ' ' + str(year))
                ax.set_xticks([0.5, 1.5])
                ax.set_xticklabels(['feedinlib', 'measurement data'])
                plt.show()


def pv_generation_test():
    '''Evaluate test of PV generation data with given reference data'''
    
    coastDat_years = [1998, 2003, 2007, 2010, 2011, 2012, 2013]
    
    # retrieve reference data
    pv_reference_data = pv_generation_reference_data()
    wind_reference_data = wind_generation_reference_data()
    
    # retrieve feedinlib data accorinding to power plants in referece data set
    pv_feedin = pv_apply_feedinlib(coastDat_years, pv_reference_data)
    wind_feedin = wind_apply_feedinlib(coastDat_years, wind_reference_data)

    #simple print for first evaluation
    simple_plot(pv_feedin, pv_reference_data, coastDat_years)
    simple_plot(wind_feedin, wind_reference_data, coastDat_years)

    
pv_generation_test()