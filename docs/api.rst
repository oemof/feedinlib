.. _api:

###
API
###


Power plant classes
====================

Power plant classes for specific weather dependent renewable energy resources.

.. autosummary::
   :toctree: temp/

   feedinlib.powerplants.Photovoltaic
   feedinlib.powerplants.WindPowerPlant

Feed-in models
===============

Feed-in models take in power plant and weather data to calculate power plant feed-in.
So far models using the python libraries pvlib and windpowerlib to calculate photovoltaic and
wind power feed-in, respectively, have been implemented.

.. autosummary::
   :toctree: temp/

   feedinlib.models.Pvlib
   feedinlib.models.WindpowerlibTurbine
   feedinlib.models.WindpowerlibTurbineCluster

Weather data
============

The feedinlib enables download of open_FRED weather data (local reanalysis data for Germany)
and ERA5 weather data (global reanalysis data for the whole world).

.. autosummary::
   :toctree: temp/

   feedinlib.open_FRED.Weather
   feedinlib.era5.weather_df_from_era5
   feedinlib.era5.get_era5_data_from_datespan_and_position

Tools
=====

.. autosummary::
   :toctree: temp/

   feedinlib.models.get_power_plant_data

Abstract classes
================

The feedinlib uses abstract classes for power plant and feed-in models that serve as blueprints
for classes that implement those models. This ensures that new models provide required
implementations that make it possible to easily exchange the model used in your calculation.
They are important for people who want to implement new power plant and model classes
rather than for users.

.. autosummary::
   :toctree: temp/

   feedinlib.powerplants.Base
   feedinlib.models.base.Base
   feedinlib.models.base.PhotovoltaicModelBase
   feedinlib.models.base.WindpowerModelBase
