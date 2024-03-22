========
Overview
========

.. start-badges

|workflow_pytests| |workflow_checks| |docs| |requires| |coveralls| |packaging|
|version| |wheel| |supported-versions| |supported-implementations| |commits-since|

.. |docs| image:: https://readthedocs.org/projects/feedinlib/badge/?style=flat
    :target: https://feedinlib.readthedocs.io/
    :alt: Documentation Status

.. |workflow_pytests| image:: https://github.com/oemof/feedinlib/workflows/tox%20pytests/badge.svg?branch=revision/add-tox-github-workflows-src-directory-ci
    :target: https://github.com/oemof/feedinlib/actions?query=workflow%3A%22tox+pytests%22

.. |workflow_checks| image:: https://github.com/oemof/feedinlib/workflows/tox%20checks/badge.svg?branch=revision/add-tox-github-workflows-src-directory-ci
    :target: https://github.com/oemof/feedinlib/actions?query=workflow%3A%22tox+checks%22

.. |packaging| image:: https://github.com/oemof/feedinlib/workflows/packaging/badge.svg?branch=revision/add-tox-github-workflows-src-directory-ci
    :target: https://github.com/oemof/feedinlib/actions?query=workflow%3Apackaging

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/oemof/feedinlib?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/oemof/feedinlib

.. |requires| image:: https://requires.io/github/oemof/feedinlib/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/oemof/feedinlib/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/github/oemof/feedinlib/badge.svg?branch=dev
    :alt: Coverage Status
    :target: https://coveralls.io/github/oemof/feedinlib?branch=dev

.. |version| image:: https://img.shields.io/pypi/v/feedinlib.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/feedinlib

.. |wheel| image:: https://img.shields.io/pypi/wheel/feedinlib.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/feedinlib

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/feedinlib.svg
    :alt: Supported versions
    :target: https://pypi.org/project/feedinlib

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/feedinlib.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/feedinlib

.. |commits-since| image:: https://img.shields.io/github/commits-since/oemof/feedinlib/v0.0.12.svg
    :alt: Commits since latest release
    :target: https://github.com/oemof/feedinlib/compare/v0.0.12...master



.. end-badges

Connect weather data interfaces with interfaces of wind and pv power models.

* Free software: MIT license

Installation
============

On Linux systems, you can just::

    pip install feedinlib

You can also install the in-development version with::

    pip install https://github.com/oemof/feedinlib/archive/master.zip
    
On Windows systems, some dependencies are not pip-installable. Thus, Windws
users first have to manually install the dependencies e.g. using conda or mamba.


Documentation
=============


https://feedinlib.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
