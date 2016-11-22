#!/usr/bin/python3
# -*- coding: utf-8

import pandas as pd
import logging
import os

try:
    from matplotlib import pyplot as plt
    plot_fkt = True
except:
    plot_fkt = False

from feedinlib import powerplants as plants
from feedinlib import weather

logging.getLogger().setLevel(logging.INFO)


class MyModel:
    'Description of your own model.'
    def __init__(self, required=['steps']):
        self.required = required

    def feedin(self, **kwargs):
        mydata = kwargs["weather"].data.v_wind * kwargs["steps"]
        return pd.Series(data=mydata,
                         index=kwargs['weather'].data.index,
                         name='my_feedin_wind_series')


# Writing your own model and passing it to the feedinlib is usefull for testing
# purpose. If you have a good alternative model we request you to publish it
# within the feedinlib or anywhere else, so that we can link to it.

# Loading weather data from csv-file.
my_weather = weather.FeedinWeather()
my_weather.read_feedinlib_csv(filename='weather_wittenberg.csv')


# Initialise your own model and apply it.
mymodel = MyModel(required=['steps'])
myplant = plants.WindPowerPlant(model=mymodel, steps=3)
myfeedin = myplant.feedin(weather=my_weather, number=2)

# Plot
if plot_fkt:
    myfeedin.plot()
    plt.show()
else:
    print(myfeedin)

logging.info('Done!')
