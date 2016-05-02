The feedinlib is designed to calculate feedin timeseries of photovoltaic and wind power plants. It is part of the oemof group but works as a standalone application.

The feedinlib is ready to use but may have some teething troubles. It definitely has a lot of space for further development, new and improved models and nice features.

.. contents:: `Table of contents`
    :depth: 1
    :local:
    :backlinks: top

Introduction
============

Having weather data sets you can use the feedinlib to calculate the electrical output of common pv or wind power plants. Basic parameters for many manufacturers are provided with the library so that you can start directly using one of these parameter sets. Of course you are free to add your own parameter set.

The parameter sets for pv modules are provided by Sandia Laboratories and can be found here:

 * https://sam.nrel.gov/sites/default/files/sam-library-sandia-modules-2015-6-30.csv
 * https://sam.nrel.gov/sites/default/files/sam-library-cec-modules-2015-6-30.csv

The cp-values for the wind turbines are provided by the Reiner Lemoine Institut and can be found here:

 * http://vernetzen.uni-flensburg.de/~git/cp_values.csv
 
If just want to use the feedinlib to calculate pv systems, you should think of using the `pvlib <https://github.com/pvlib/pvlib-python>`_ directly. At the moment the pv part of the feedinlib is just a high level (easy to use) interface for same pvlib functionalities.

Actual Release
~~~~~~~~~~~~~~

Download/Install: https://pypi.python.org/pypi/feedinlib/

Documentation: http://pythonhosted.org/feedinlib/

Developing Version
~~~~~~~~~~~~~~~~~~

Clone/Fork: https://github.com/oemof/feedinlib

Documentation: http://feedinlib.readthedocs.org/en/latest/

As the feedinlib is part of the oemof developer group we use the same developer rules:
http://oemof.readthedocs.io/en/stable/developer_notes.html

Installation
============

Using the Feedinlib
~~~~~~~~~~~~~~~~~~~

So far, the feedinlib is mainly tested on python 3.4 but seems to work down
to 2.7.

Install the feedinlib using pip3 (or pip2).

::

    sudo pip3 install feedinlib

Developing the Feedinlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have push rights clone this repository to your local system.

::

    git clone git@github.com:oemof/feedinlib.git
    
If you do not have push rights, fork the project at github, clone your personal fork to your system and send a pull request.

If the project is cloned you can install it using pip3 (or pip2) with the -e flag. Using this installation, every change is applied directly.

::

    sudo pip3 install -e <path/to/the/feedinlib/root/dir>
    
  
Optional Packages
~~~~~~~~~~~~~~~~~

To see the plots of the example file one should install the matplotlib package.

Matplotlib can be installed using pip but some Linux users reported that it is easier and more stable to use the pre-built packages of your Linux distribution.

http://matplotlib.org/users/installing.html

Example
~~~~~~~~~~~~~~~~~~~~~~~~
Download the example file and execute it:

http://vernetzen.uni-flensburg.de/~git/feedinlib_example.py


Basic Usage
===========

You need three steps to get a time series.

Warning
~~~~~~~
Be accurate with the units. In the example all units are given without a prefix.
 * pressure [Pa]
 * wind speed [m/s]
 * irradiation [W/m²]
 * peak power [W]
 * installed capacity [W]
 * nominal power [W]
 * area [m²]

You can also use kW instead of W but you have to make sure that all units change in the same way.

1. Initialise your Turbine or Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To initialise your specific module or turbine you need a dictionary that contains your basic parameters. 

The most import parameter is the name of the module or turbine to get technical parameters from the provided libraries.

The other parameters are related to location of the plant like orientation of the pv module or the hub height of the wind turbine. The existing models need the following parameters:

Wind Model
++++++++++

 * h_hub: height of the hub in meters
 * d_rotor: diameter of the rotor in meters
 * wind_conv_type: Name of the wind converter according to the list in the csv file

PV Model
++++++++

 * azimuth: Azimuth angle of the pv module in degree
 * tilt: Tilt angle of the pv module in degree
 * module_name: According to the sandia module library (see the link above)
 * albedo: Albedo value

.. code:: python

    your_wind_turbine = plants.WindPowerPlant(model=SimpleWindModel, **your_parameter_set)
    your_pv_module = plants.Photovoltaic(model=PvlibBased, **your_parameter_set)
    
If you do not pass a model the default model is used. So far we only have one model, so the follwing lines will have the same effect than the lines above.


 .. code:: python

    your_wind_turbine = plants.WindPowerPlant(**your_parameter_set)
    your_pv_module = plants.Photovoltaic(**your_parameter_set)
       
2. Initialise a weather object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A weather object contains one weather data set and all its necessary meta data. You can define it passing all the information from your weather data source to the FeedinWeatehr class.

.. code:: python

    my_weather_a = weather.FeedinWeather(
        data=my_weather_pandas_DataFrame,
        timezone='Continent/City',  # e.g. Europe/Berlin or America/Caracas
        latitude=x,  # float 
        longitude=y,  # float
        data_heigth=coastDat2  # Dictionary, for the data heights (see below).
        )

Depending on the model you do not need all of the optional parameters. For example the standard wind model does not need the longitude. If the DataFrame has a full time index with a time zone you don't have to set the time zone.

For wind and pv calculations the DataFrame needs to have radiation, temperature and wind speed for the pv model and pressure, wind speed, temperature and the roughness length for the wind model.

The data_height dictionary should be of the following form.

.. code:: python  
     
    coastDat2 = {
        'dhi': 0,
        'dirhi': 0,
        'pressure': 0,
        'temp_air': 2,
        'v_wind': 10,
        'Z0': 0}
        
If your DataFrame has different column names you have to rename them. This can easily be done by using a conversion dictionary:

.. code:: python

    name_dc = {
        'your diffuse horizontal radiation': 'dhi',
        'your direct horizontal radiation': 'dirhi',
        'your pressure data set': 'pressure',
        'your ambient temperature': 'temp_air',
        'your wind speed': 'v_wind',
        'your roughness length': 'z0'}
    
    your_weather_DataFrame.rename(columns=name_dc)
    
3. Get your Feedin Time Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get your time series you have to pass the weather object to your model. If you pass only the weather object, you get the electrical output of the turbine or module specified by your parameters. You can use optional parameters to calculated more than one module or turbine.
 
The possible parameters are *number* and *installed capacity* for wind turbines and *number*, *peak_power* and *area* for pv modules.
 
.. code:: python
 
    feedin_series_pv1 = your_pv_module.feedin(weather=my_weather_df)  # One Module
    feedin_series_wp1 = your_wind_turbine.feedin(data=my_weather_df, number=5)
    
You always should know the nominal power, area or peak_power of your plant. An area of two square meters (area=2) of a specific module that has an area of 1.5 sqm per module might not be realistic. 

4. Using your own model
~~~~~~~~~~~~~~~~~~~~~~~

If you use your own model it is safer to pass a list of the required parameters but you don't have to:

.. code:: python

    own_wind_model = models.YourWindModelClass(required=[parameter1, parameter2])
    own_pv_model = models.YourPVModelClass()
    
    your_wind_turbine = plants.WindPowerPlant(model=own_wind_model, **your_parameter_set)
    your_pv_module = plants.Photovoltaic(model=own_pv_model, **your_parameter_set)
    
    feedin_series_wp1 = your_wind_turbine.feedin(data=my_weather_df, number=5)
    feedin_series_pv1 = your_pv_module.feedin(data=my_weather_df)  # One Module
   
