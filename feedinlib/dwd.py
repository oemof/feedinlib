"""
@author: pyosch

Convert dwd irradiation data for use with PVlib.

PVlib:
    https://github.com/pvlib/pvlib-python

Convert dwd wind, temperature and pressure data for use with windpowerlib.

windpowerlib:
    https://github.com/wind-python/windpowerlib

Convert dwd temperature data for heat demand and cop calculations in vpplib

vpplib:
    https://github.com/Pyosch/vpplib

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# define the times for which the data should be extracted
start= "2015-01-01 00:00:00"
end = "2015-12-31 23:45:00"
resample_to = '15 Min'

temperature_file = "produkt_zehn_min_tu_20100101_20181231_02667.txt"
"""
Note:
The temperature_file contains temperature and air pressure

Resource:
ftp://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/
10_minutes/air_temperature/historical/
"""

pv_file = 'produkt_zehn_min_sd_20100101_20181231_02667.txt'
"""
Resource:
ftp://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/
10_minutes/solar/historical/
"""

wind_file = 'produkt_zehn_min_ff_20100101_20181231_02667.txt'
"""
Resource:
ftp://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/
10_minutes/wind/historical/
"""

# destination for extracted results
temp_output_file = "dwd_temp_15min.csv"
temp_hours_output_file = "dwd_temp_hours.csv"
temp_days_output_file = "dwd_temp_days.csv"
wea_output_file = ".dwd_wind_data.csv"
pv_output_file = "dwd_pv_data.csv"

# location specific roughness length for wind
roughness_length = 0.15

# plot
figsize = (10,6)


def dwd_read(file):
    
    df = pd.read_csv(file, sep=";", index_col="MESS_DATUM")
    df.index = pd.to_datetime(df.index, format='%Y%m%d%H%M')
    
    return df


def dwd_process(df, drop, rename, start, end, resample_to):
    
    df.rename(columns=rename, inplace=True)
    df.drop(drop, axis=1, inplace=True)
    
    df_resample = df.resample(resample_to).mean()
    df_resample = df_resample[start:end]
    df_resample.index.rename("time", inplace=True)
    
    return df_resample


#%% temperature and pressure

"""
Es stehen folgende Parameter zur Verfügung:
    
STATIONS_ID     Stationsidentifikationsnummer
MESS_DATUM      Zeitstempel yyyymmddhhmi
QN              Qualitätsniveau der nachfolgenden Spalten code siehe Absatz 
                "Qualitätsinformation"
PP_10           Luftdruck auf Stationshöhe hPa
TT_10           Lufttemperatur in 2m Höhe °C
TM5_10          Lufttemperatur 5cm Höhe °C
RF_10           relative Feuchte in 2m Höhe %
TD_10           Taupunkttemperatur in 2m Höhe °C
eor             Ende data record

Fehlwerte sind mit -999 gekennzeichnet. 
Die Messungen sind vor dem Jahr 2000 einem Zeitstempel in MEZ zugeordnet, 
ab dem Jahr 2000 einem Zeitstempel in UTC. 
Die Taupunktstemperatur ist aus der Lufttemperatur in 2m Höhe und 
der relativen Feuchtemessungen berechnet. 
Die Werte sind Mittelwerte die Minute, welche zum Zeitstempel endet. 
Der Zeitstempel ist vor dem Jahr 2000 in MEZ gegeben, ab dem Jahr 2000 in UTC.
"""

temp_drop = ['STATIONS_ID', '  QN', 'TM5_10', 'RF_10', 'TD_10', 'eor']
temp_rename = {"PP_10":"pressure", "TT_10":"temperature"}

df_temp = dwd_read(temperature_file)
df_temp_resample = dwd_process(df=df_temp, drop=temp_drop, rename=temp_rename,
                               start=start, end=end, resample_to=resample_to)

# Interpolate over wrong measurements
df_temp_resample.where(cond=(df_temp_resample.temperature>-30.0),
                       other=None, inplace=True)
df_temp_resample.where(cond=(df_temp_resample.pressure>800.0),
                       other=None, inplace=True)
df_temp_resample.interpolate(inplace=True)

df_temp_resample.plot(figsize=figsize)
plt.show()

"""
Restructuring data and conversion of units for heat demand and cop calculations
for heat pump
"""

df_temp_mean_hours = pd.DataFrame(
        df_temp_resample.temperature.resample("h").mean(),
        columns=["temperature"])
df_temp_mean_days = pd.DataFrame(
        df_temp_resample.temperature.resample("d").mean(),
        columns=["temperature"])

df_temp_15min = pd.DataFrame(df_temp_resample.temperature)
df_temp_15min.to_csv(temp_output_file)
df_temp_mean_hours.to_csv(temp_hours_output_file)
df_temp_mean_days.to_csv(temp_days_output_file)

#%% photovoltaic

"""
In produkt*.txt stehen folgende Parameter zur Verfügung:
STATIONS_ID     Identifikationsnummer der Station
MESS_DATUM      Intervallende in UTC [yyyymmddhhmi]
QN              Qualitätsniveau der nachfolgenden Spalten code siehe Absatz
                "Qualitätsinformation"
DS_10           10min-Summe der diffusen solaren Strahlung [J/cm^2]
GS_10           10min-Summe der Globalstrahlung [J/cm^2]
SD_10           10min-Summe der Sonnenscheindauer [h]
LS_10           10min-Summe der atmosphärischen Gegenstrahlung [J/cm^2]

Fehlwerte sind mit -999 gekennzeichnet.
Die Messungen sind einem Zeitstempel zugeordnet, welcher das Ende des
zehnminütigen Intervalles markiert. Die Globalstrahlung umfasst den direkten
und diffusen Anteil der solaren Strahlung bezogen auf die Horizontalfläche.
Manchmal wird "Globalstrahlung" auch mit der Bezeichnung "kurzwellig"
verknüpft, dabei ist bis zu 2.8 Mikometer gemeint, denn in diesem Zusammenhang
bezieht sich "kurzwellig" auf das solare Spektrum, im Gegensatz zu "langwellig"
als Bezeichnung des Spektrums der Wärmestrahlung der Atmosphäre.
Der Zeitstempel ist vor dem Jahr 2000 in MEZ gegeben, ab dem Jahr 2000 in UTC.
"""

# sort out irrelevant data
pv_drop = ['STATIONS_ID', '  QN', 'SD_10', 'LS_10', 'eor']
pv_rename = {"DS_10": "dhi", "GS_10": "ghi"}

df_pv = dwd_read(pv_file)
df_pv_resample = dwd_process(df=df_pv, drop=pv_drop, rename=pv_rename,
                               start=start, end=end, resample_to=resample_to)

# Interpolate over wrong measurements
df_pv_resample.where(cond=(df_pv_resample>=0.0), other=None, inplace=True)
df_pv_resample.interpolate(inplace=True)

print(df_pv_resample.head())
df_pv_resample.plot(figsize=figsize)
plt.show()


"""
Restructuring data and conversion of units for use with pvlib

change from J/cm^2 to W/m^2
J = Ws ; 10min = 600s ; 10000 cm^2 = m^2
Ws/cm^2 *10000/600s = 100/6 W/m^2 if
"""

df_pv_resample.ghi = pd.DataFrame(df_pv_resample.ghi *100/6)
df_pv_resample.dhi = pd.DataFrame(df_pv_resample.dhi *100/6)

# calculate direct normal irradiation
df_pv_resample['dni'] = df_pv_resample.ghi - df_pv_resample.dhi


print(df_pv_resample.head())
df_pv_resample.plot(figsize=figsize)
plt.show()
df_pv_resample.to_csv(pv_output_file)

#%% wind

"""
Es stehen folgende Parameter zur Verfügung:
    
STATIONS_ID     Stationsidentifikationsnummer
MESS_DATUM_ENDE Intervallende yyyymmddhhmi
QN              Qualitätsniveau der nachfolgenden Spalten code siehe Absatz
                "Qualitätsinformation"
FF_10           10min-Mittel der Windgeschwindigkeit m/s
DD_10           10min-Mittel der Windrichtung Grad
eor             Ende data record

Fehlwerte sind mit -999 gekennzeichnet.
Die Messungen sind einem Zeitstempel zugeordnet,
welcher das Ende des zehnminütigen Intervalles markiert.
Der Zeitstempel ist vor dem Jahr 2000 in MEZ gegeben, ab dem Jahr 2000 in UTC.
"""

wind_drop = ['STATIONS_ID','  QN','DD_10','eor']
wind_rename = {"FF_10":"wind_speed"}

df_wind = dwd_read(wind_file)
df_wind_resample = dwd_process(df=df_wind, drop=wind_drop, rename=wind_rename,
                               start=start, end=end, resample_to=resample_to)
#Interpolate over wrong measurements
df_wind_resample.where(cond=(df_wind_resample>0.0), other=None, inplace=True)
df_wind_resample.interpolate(inplace=True)

df_wind_resample.plot(figsize=figsize)
plt.show()

"""
Restructuring data for use with windpowerlib
merging of data frames and conversion of units
"""

# Height for: wind, pressure, temperature, roughness length
# See dwd documentation for details on the first three
height = [10,0,2,0]

# merge temp, pressure and wind speed for windenergy simulations
df_wea = pd.merge(left=df_wind_resample, right=df_temp_resample,
                  on="time")

df_wea["roughness_length"] = roughness_length

# create MuliIndex columns with height of measured values,
# as required by windpowerlib
df_wea_mi = pd.DataFrame(columns=[df_wea.columns, np.array(height)])
df_wea_mi.wind_speed = df_wea.wind_speed 
df_wea_mi.pressure = df_wea.pressure * 100 # hPa to Pa
df_wea_mi.temperature = df_wea.temperature + 274.15 # °C to K
df_wea_mi.roughness_length = df_wea.roughness_length

print(df_wea_mi.head())
df_wea_mi.plot(figsize=figsize)
df_wea_mi.to_csv(wea_output_file)
