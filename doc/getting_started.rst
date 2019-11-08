~~~~~~~~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~~~~~~~~

The feedinlib is designed to calculate feed-in time series of photovoltaic and wind power plants.
It is part of the oemof group but works as a standalone application.

The feedinlib is ready to use but it definitely has a lot of space for
further development, new and improved models and nice features.

Introduction
============

* so far the feedinlib provides interfaces to download open_FRED and ERA5 weather data
* open_FRED data is local reanalysis data for Germany (and bounding box). further information can be found at...
* ERA5 provides global reanalysis data. further information can be found at...
* the weather data can be used to calculate the electrical output of pv or wind power plants.
* at the moment it provides interfaces to the pvlib and the windpowerlib
* Basic parameters for many manufacturers are provided with the library so that you can start directly using one of these parameter sets.
* for further information see function get_power_plant_data
* the feedinlib is designed in such a way, that the application of different feed-in models with different weather data sets can be done easily

Installation
============

If you have a working Python 3 environment, use pip to install the latest feedinlib version:

::

    pip install feedinlib

The feedinlib is designed for Python 3 and tested on Python >= 3.5.

We highly recommend to use virtual environments.
Please see the `installation page <http://oemof.readthedocs.io/en/stable/installation_and_setup.html>`_ of the oemof documentation for complete instructions on how to install python and a virtual environment on your operating system.

Optional Packages
~~~~~~~~~~~~~~~~~

can be installed using pip:

::

    pip install ..





Examples and basic usage
=========================

The basic usage of the feedinlib is shown in the :ref:`examples_section_label` section.
The examples are provided as jupyter notebooks that you can download here:

 * :download:`open_FRED weather data example <../example/load_open_fred_weather_data.ipynb>`
 * :download:`Pvlib model example <../example/run_pvlib_model.ipynb>`

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
`developer rules <http://oemof.readthedocs.io/en/stable/developing_oemof.html>`_.

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
