.. image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/oemof/feedinlib/dev

The feedinlib is a tool to calculate feed-in time series of photovoltaic
and wind power plants. It therefore provides interfaces between
different weather data sets and feed-in models. It is part of the oemof
group but works as a standalone application.

The feedinlib is ready to use but it definitely has a lot of space for
further development, new and improved models and nice features.


Introduction
============

So far the feedinlib provides interfaces to download *open_FRED* and
`ERA5`_ weather data. *open_FRED* is a local reanalysis weather data set
that provides weather data for Germany (and bounding box). *ERA5* is a
global reanalysis weather data set that provides weather data for the
whole world. The weather data can be used to calculate the electrical
output of PV and wind power plants. At the moment the feedinlib provides
interfaces to the `pvlib`_ and the `windpowerlib`_. Furthermore,
technical parameters for many PV modules and inverters, as well as wind
turbines, are made available and can be easily used for calculations.

.. _ERA5: https://confluence.ecmwf.int/display/CKB/ERA5+data+documentation
.. _pvlib: https://github.com/pvlib/pvlib-python
.. _windpowerlib: https://github.com/wind-python/windpowerlib


Documentation
=============

Full documentation can be found at `readthedocs`_. Use the `project
site`_ of readthedocs to choose the version of the documentation. Go to
the `download page`_ to download different versions and formats (pdf,
html, epub) of the documentation.

.. _readthedocs: https://feedinlib.readthedocs.io/en/stable/
.. _project site: https://readthedocs.org/projects/feedinlib/
.. _download page: https://readthedocs.org/projects/feedinlib/downloads/


Installation
============

If you have a working Python 3 environment, use pip to install the
latest feedinlib version:

.. code::

    pip install feedinlib

The feedinlib is designed for Python 3 and tested on Python >= 3.5.

We highly recommend to use virtual environments. Please see the
`installation page`_ of the oemof documentation for complete
instructions on how to install python and a virtual environment on your
operating system.

.. _installation page:
  http://oemof.readthedocs.io/en/stable/installation_and_setup.html


Examples and basic usage
========================

The basic usage of the feedinlib is shown in the `examples`_ section of
the documentation. The examples are provided as jupyter notebooks that
you can download here:

 * `Load ERA5 weather data example`_
 * `Load open_FRED weather data example`_
 * `pvlib model example`_
 * `windpowerlib model example`_

Furthermore, you have to install the feedinlib with additional packages
needed to run the notebooks, e.g. ``jupyter``:

.. code::

    pip install feedinlib[examples]

To launch jupyter notebook type ``jupyter notebook`` in the terminal.
This will open a browser window. Navigate to the directory containing
the notebook(s) to open it. See the jupyter notebook quick start guide
for more information on `how to run`_ jupyter notebooks.

.. _examples: https://feedinlib.readthedocs.io/en/stable/examples.html
.. _Load ERA5 weather data example: https://raw.githubusercontent.com/oemof/feedinlib/master/example/load_era5_weather_data.ipynb
.. _Load open_FRED weather data example: https://raw.githubusercontent.com/oemof/feedinlib/master/example/load_open_fred_weather_data.ipynb
.. _pvlib model example: https://raw.githubusercontent.com/oemof/feedinlib/master/example/run_pvlib_model.ipynb
.. _windpowerlib model example: https://raw.githubusercontent.com/oemof/feedinlib/master/example/run_windpowerlib_turbine_model.ipynb
.. _how to run: http://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/execute.html


Contributing
============

We are warmly welcoming all who want to contribute to the feedinlib. If
you are interested do not hesitate to contact us via github.

As the feedinlib started with contributors from the `oemof developer
group`_ we use the same `developer rules`_.

.. _oemof developer group: https://github.com/orgs/oemof/teams/oemof-developer-group
.. _developer rules: http://oemof.readthedocs.io/en/stable/developing_oemof.html>


**How to create a pull request:**

* `Fork`_ the feedinlib repository to your own github account.
* Create a local clone of your fork and  install the cloned repository
  using pip with the ``-e`` option:

  .. code::

      pip install -e /path/to/the/repository

* Change, add or remove code.
* Commit your changes.
* Create a `pull request`_ and describe what you will do and why.
* Wait for approval.

.. _Fork: https://help.github.com/articles/fork-a-repo
.. _pull request: https://guides.github.com/activities/hello-world/

**Generally the following steps are required when changing, adding or
removing code:**

* Add new tests if you have written new functions/classes.
* Add/change the documentation (new feature, API changes ...).
* Add a whatsnew entry and your name to Contributors.
* Check if all tests still work by simply executing pytest in your
  feedinlib directory:

  .. code::

      pytest


Citing the feedinlib
====================

We use the zenodo project to get a DOI for each version.
`Search zenodo for the right citation of your feedinlib version`_.

.. _Search zenodo for the right citation of your feedinlib version:
  https://zenodo.org/record/2554102


License
=======

MIT License

Copyright (C) 2017 oemof developer group
