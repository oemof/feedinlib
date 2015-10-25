#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 17:10:54 2015

@author: guido

Works only if oemof is installed and database with coastDat2 dataset is 
available
"""

from oopmof.src import db
from oopmof.src import energy_weather as w
from feedinlib import powerplants as plants
from feedinlib import models
from shapely.geometry import Point, Polygon
import logging


def pv_generation_reference_data():
    '''returns a dict containing reference data at different locations'''
    reference_data = {
        'pv_biesdorf': { # runs with CEC
#            'module_name': 'Sovello_SV_X_205_yyy', #original module
            'module_name': 'SunPower_SPR_205_BLK__2007__E__',
            'capacity': 7.640,
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
            'h_hub': 70.5, #135, # estimated by http://en.wind-turbine-models.com/turbines/114-enercon-e-58-10.58
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


def pv_apply_feedinlib(reference_data=None):

    # get reference data
    if reference_data is None:
        reference_data = pv_generation_reference_data()

    # get database connection
    conn = db.connection()

    required_parameter_pv = {
        'azimuth': 'Azimuth angle of the pv module',
        'tilt': 'Tilt angle of the pv module',
        'module_name': 'According to the sandia module library.',
        'albedo': 'Albedo value',
        'tz': 'Time zone',
        'longitude': 'Position of the weather data (longitude)',
        'latitude': 'Position of the weather data (latitude)'}
    pv_feedin_annual = {}
    
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
        coastDat_years = [1998, 2003, 2007, 2010, 2011, 2012, 2013]

        # instantiate modelKyocera_Solar_KD205GX_LP
        pv_model = models.Photovoltaic(required=list(required_parameter_pv.keys())) 
        
        # choose module type and add location
        module_type = {'module_name': reference_data[unit]['module_name'],
                       'azimuth': reference_data[unit]['azimuth'],
                        'tilt': reference_data[unit]['tilt'],
                        'albedo': 0.2,
                        'latitude': reference_data[unit]['location']['lat'],
                        'longitude': reference_data[unit]['location']['lon'],
                        'tz': reference_data[unit]['tz']}
        pv_module = plants.Photovoltaic(model=pv_model, **module_type)

        for year in set(years).intersection(coastDat_years):
            # get weather data
            my_weather_df = w.Weather(conn, Point(
                reference_data[unit]['location']['lon'],
                reference_data[unit]['location']['lat']), 
                int(year)
                ).get_feedin_data()
            if reference_data[unit].get('module_number') is not None:
                pv_feedin_annual[unit][year] = pv_module.feedin(
                    data=my_weather_df, 
                    number=reference_data[unit]['module_number']).sum() / 1e3
            elif reference_data[unit].get('capacity') is not None:
                pv_feedin_annual[unit][year] = pv_module.feedin(data=my_weather_df, 
                    peak_power=reference_data[unit]['capacity']).sum() / 1e3
            else:
                print('at least supply `module_number` or `capacity`')
    return pv_feedin_annual
    
    
def wind_apply_feedinlib(reference_data):
    required_parameter_wind = {
        'h_hub': 'height of the hub in meters',
        'd_rotor': 'diameter of the rotor in meters',
        'wind_conv_type': 'wind converter according to the list in the csv file.',
        'data_height': 'dictionary containing the heights of the data model'}
    coastDat2 = {
        'dhi': 0,
        'dirhi': 0,
        'pressure': 0,
        'temp_air': 2,
        'v_wind': 10,
        'Z0': 0}
        
    # get database connection
    conn = db.connection()
        
    # iterate over passed reference data dict
    wind_feedin_annual = {}
    for unit in list(reference_data.keys()):
        wind_feedin_annual[unit] = {} 
    
        years = [int(y) for y in reference_data[unit]['generation']]
        coastDat_years = [1998, 2003, 2007, 2010, 2011, 2012, 2013]

        # instantiate modelKyocera_Solar_KD205GX_LP
        generic_wind_model = models.WindPowerPlant(
            required=list(required_parameter_wind.keys()))
            
        wind_model = plants.WindPowerPlant(model=generic_wind_model, **{
            'h_hub': reference_data[unit]['h_hub'],
            'd_rotor': reference_data[unit]['d_rotor'],
            'wind_conv_type': reference_data[unit]['wind_conv_type'],
            'data_height': coastDat2})

        for year in set(years).intersection(coastDat_years):
            # get weather data
            my_weather_df = w.Weather(conn, Point(
                reference_data[unit]['location']['lon'],
                reference_data[unit]['location']['lat']), 
                int(year)
                ).get_feedin_data()
            if reference_data[unit].get('number') is not None:
                wind_feedin_annual[unit][year] = wind_model.feedin(
                    data=my_weather_df, 
                    number=reference_data[unit]['number']).sum() / 1e6
            elif reference_data[unit].get('capacity') is not None:
                wind_feedin_annual[unit][year] = wind_model.feedin(data=my_weather_df, 
                    installed_capacity=reference_data[unit]['capacity']).sum()/1e6
            else:
                print('at least provide `number` or `capacity`')
    return wind_feedin_annual


def simple_evaluation_print(feedin, reference_data, coastDat_years):

    for year in coastDat_years:
        print('======= ' + str(year) + ' =======')
        print('Unit\t\t\tReference\tfeedinlib\tRatio')
        for unit in list(feedin.keys()):
            reference_data_years = [int(x) for x in list(
                reference_data[unit]['generation'].keys())],
            feedin_years = list(feedin[unit].keys())
            if ((year in reference_data_years[0]) and (year in feedin_years)):
                print('{3}\t\t{0:.0f}\t\t{1:.0f}\t\t{2:.2f}'.format(
                    reference_data[unit]['generation']
                    [str(year)], feedin[unit][year],
                    feedin[unit][year] / reference_data[unit]['generation']
                    [str(year)], unit))
        


def pv_generation_test():
    '''Evaluate test of PV generation data with given reference data'''
    
    coastDat_years = [1998, 2003, 2007, 2010, 2011, 2012, 2013]
    
    # retrieve reference data
    pv_reference_data = pv_generation_reference_data()
    wind_reference_data = wind_generation_reference_data()
    
    # retrieve feedinlib data accorinding to power plants in referece data set
    pv_feedin = pv_apply_feedinlib(pv_reference_data)
    wind_feedin = wind_apply_feedinlib(wind_reference_data)
    
    #simple print for first evaluation
    print('######## PV ########')
    simple_evaluation_print(pv_feedin, pv_reference_data, coastDat_years)
    print('######## WIND ########')
    simple_evaluation_print(wind_feedin, wind_reference_data, coastDat_years)
    
pv_generation_test()