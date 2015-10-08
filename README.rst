The feedinlib is designed to calculate feedin timeseries of photovoltaic and wind power plants.

The feedinlib is ready to use but may have some teething troubles. It definitely has a lot of space for further development, new and improved models and nice features.

.. contents:: `Table of contents`
    :depth: 1
    :local:
    :backlinks: top

Introduction
============

Having weather data sets you can use the feedinlib to calculate the electrical output of common pv or wind power plants. Basic parameters for many manufacturers are provided with the library so that you can start directly using one of these parameter sets. Of course you are free to add your own parameter set.

The parameter sets for pv modules are provided by Sandia Laboratories and can be found here:

 * https://sam.nrel.gov/sites/sam.nrel.gov/files/sam-library-sandia-modules-2015-6-30.csv
 * https://sam.nrel.gov/sites/sam.nrel.gov/files/sam-library-cec-modules-2015-6-30.csv

The cp-values for the wind turbines are provided by the Reiner Lemoine Institut and can be found here:

 * http://vernetzen.uni-flensburg.de/~git/cp_values.csv

Actual Release
~~~~~~~~~~~~~~

Download/Install: https://pypi.python.org/pypi/feedinlib/

Documentation: http://pythonhosted.org/feedinlib/

Developing Version
~~~~~~~~~~~~~~~~~~

Clone/Fork: https://github.com/oemof/feedinlib

Documentation: http://feedinlib.readthedocs.org/en/latest/

Installation
============

Using the Feedinlib
~~~~~~~~~~~~~~~~~~~

So far, the feedinlib is mainly tested on python 3.4 but seems to work down
to 2.7.

Install the feedinlib using pip (or pip3).

::

    sudo pip install feedinlib

Developing the Feedinlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have push rights clone this repository to your local system.

::

    git clone git@github.com:oemof/feedinlib.git
    
If you do not have push rights, fork the project at github, clone your personal fork to your system and send a pull request.

If the project is cloned you can install it using pip (or pip3) with the -e flag. Using this installation, every change is applied directly.

::

    sudo pip install -e <path/to/the/feedinlib/root/dir>
    
you
    
  
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

1. Initialise a Model
~~~~~~~~~~~~~~~~~~~~~

It is safer to pass a list of the required parameters but you don't have to:

::

    wp_model = models.WindPowerPlant(required=[])
    pv_model = models.Photovoltaic(required=[])
    
In future versions this is the place where you can initialise different pv or wind models.

2. Initialise your Turbine or Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To initialise your specific module or turbine you need a dictionary that contains your basic parameters. 

The most import parameter is the name of the module or turbine to get technical parameters from the provided libraries.

The other parameters are related to location of the plant like orientation of the pv module or the hub height of the wind turbine. The existing models need the following parameters:

Wind Model
++++++++++

 * h_hub: height of the hub in meters
 * d_rotor: diameter of the rotor in meters
 * wind_conv_type: Name of the wind converter according to the list in the csv file
 * data_height: dictionary containing the heights of the data model

PV Model
++++++++

 * azimuth: Azimuth angle of the pv module in degree
 * tilt: Tilt angle of the pv module in degree
 * module_name: According to the sandia module library (see the link above)
 * albedo: Albedo value
 * tz: Time zone, where the weather data set is located
 * longitude: Position of the weather data (longitude)
 * latitude: Position of the weather data (latitude)

::

    your_wind_turbine = plants.WindPowerPlant(model=wp_model, **your_parameter_set)
    your_pv_module = plants.Photovoltaic(model=pv_model, **your_parameter_set)
    
3. Get your Feedin Time Series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get your time series you have to pass the weather data to your model. The weather data should contain the following time series and must be named as follows. If your DataFrame has different names you can easily rename it:

::

    name_dc = {
        'your diffuse horizontal radiation': 'dhi',
        'your direct horizontal radiation': 'dirhi',
        'your pressure data set': 'pressure',
        'your ambient temperature': 'temp_air',
        'your wind speed': 'v_wind',
        'your roughness length': 'z0'}
    
    your_weather_DataFrame.rename(columns=name_dc)
    
You need radiation, temperature and wind speed for the pv model and pressure, wind speed, temperature and the roughness length for the wind model.
 
If you pass just the weather data, you get the electrical output of the turbine or module specified by your parameters. You can use optional parameters to calculated more than one module or turbine.
 
The possible parameters are *number* and *installed capacity* for wind turbines and *number*, *peak_power* and *area* for pv modules.
 
::
 
    feedin_series_pv1 = your_pv_module.feedin(data=my_weather_df)  # One Module
    feedin_series_wp1 = your_wind_turbine.feedin(data=my_weather_df, number=5)
    
You always should know the nominal power, area or peak_power of your plant. An area of two square meters (area=2) of a specific module that has an area of 1.5 sqm per module might not be realistic. 

