.. _api:

#############
API
#############


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

Tools
====================

.. autosummary::
   :toctree: temp/

   feedinlib.models.get_power_plant_data

Abstract classes
====================

The feedinlib uses abstract classes for power plant and feed-in models that serve as blueprints
for classes that implement those models. This ensures that new models provide required
implementations that make it possible to easily exchange the model used in your calculation.
They are important for people who want to implement new power plant and model classes 
rather than for users.

.. autosummary::
   :toctree: temp/

   feedinlib.powerplants.Base
   feedinlib.models.Base
   feedinlib.models.PhotovoltaicModelBase
   feedinlib.models.WindpowerModelBase