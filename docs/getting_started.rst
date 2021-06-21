.. include:: ../README.rst

The feedinlib is designed to calculate feed-in time series of photovoltaic and wind power plants.
It is part of the oemof group but works as a standalone application.

The feedinlib is ready to use but it definitely has a lot of space for
further development, new and improved models and nice features.

Introduction
============

So far the feedinlib provides interfaces to download *open_FRED* and
`ERA5 <https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation>`_ weather data.
*open_FRED* is a local reanalysis weather data set that provides weather data for Germany (and bounding box).
*ERA5* is a global reanalysis weather data set that provides weather data for the whole world.
The weather data can be used to calculate the electrical output of PV and wind power plants.
At the moment the feedinlib provides interfaces to the `pvlib <https://github.com/pvlib/pvlib-python>`_ and the
`windpowerlib <https://github.com/wind-python/windpowerlib>`_.
Furthermore, technical parameters for many PV modules and inverters,
as well as wind turbines, are made available and can be easily used for calculations.

Installation
============

If you have a working Python 3 environment, use pip to install the latest feedinlib version:

::

    pip install feedinlib

The feedinlib is designed for Python 3 and tested on Python >= 3.6.

We highly recommend to use virtual environments.


Examples and basic usage
=========================

The basic usage of the feedinlib is shown in the :ref:`examples_section_label` section.
The examples are provided as jupyter notebooks that you can download here:

 * :download:`ERA5 weather data example <../examples/load_era5_weather_data.ipynb>`
 * :download:`open_FRED weather data example <../examples/load_open_fred_weather_data.ipynb>`
 * :download:`pvlib model example <../examples/run_pvlib_model.ipynb>`
 * :download:`windpowerlib model example <../examples/run_windpowerlib_turbine_model.ipynb>`

Furthermore, you have to install the feedinlib with additional packages needed to run the notebooks, e.g. `jupyter`.

::

    pip install feedinlib[examples]

To launch jupyter notebook type ``jupyter notebook`` in the terminal.
This will open a browser window. Navigate to the directory containing the notebook(s) to open it. See the jupyter
notebook quick start guide for more information on
`how to run <http://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/execute.html>`_ jupyter notebooks.

Contributing
==============

We are warmly welcoming all who want to contribute to the feedinlib. If you are interested
do not hesitate to contact us via github.

As the feedinlib started with contributors from the
`oemof developer group <https://github.com/orgs/oemof/teams/oemof-developer-group>`_
we use the same
`developer rules <https://oemof.readthedocs.io/en/latest/contributing.html>`_.

**How to create a pull request:**

* `Fork <https://help.github.com/articles/fork-a-repo>`_ the feedinlib repository to your own github account.
* Create a local clone of your fork and  install the cloned repository using pip with -e option:

.. code:: bash

  pip install -e /path/to/the/repository

* Change, add or remove code.
* Commit your changes.
* Create a `pull request <https://guides.github.com/activities/hello-world/>`_ and describe what you will do and why.
* Wait for approval.

**Generally the following steps are required when changing, adding or removing code:**

* Add new tests if you have written new functions/classes.
* Add/change the documentation (new feature, API changes ...).
* Add a whatsnew entry and your name to Contributors.
* Check if all tests still work by simply executing pytest in your feedinlib directory:

.. role:: bash(code)
   :language: bash

.. code:: bash

    pytest

Citing the feedinlib
========================

We use the zenodo project to get a DOI for each version.
`Search zenodo for the right citation of your feedinlib version <https://zenodo.org/record/2554102>`_.

License
============

MIT License

Copyright (C) 2017 oemof developer group
