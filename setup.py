#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8"),
    ) as fh:
        return fh.read()


setup(
    name="feedinlib",
    version="0.1.0rc4",
    license="MIT",
    description=(
        "Connect weather data interfaces with interfaces of wind and pv power "
        "models."
    ),
    long_description="%s\n%s"
    % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.rst")
        ),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    long_description_content_type="text/x-rst",
    author="oemof developer group",
    author_email="contact@oemof.org",
    url="https://github.com/oemof/feedinlib",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list:
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        "Topic :: Utilities",
    ],
    project_urls={
        "Documentation": "https://feedinlib.readthedocs.io/",
        "Changelog": (
            "https://feedinlib.readthedocs.io/en/latest/changelog.html"
        ),
        "Issue Tracker": "https://github.com/oemof/feedinlib/issues",
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires=">=3.6",
    install_requires=[
        "cdsapi >= 0.1.4",
        "geopandas",
        "numpy >= 1.17.0",
        "oedialect >= 0.0.6.dev0",
        "pvlib >= 0.7.0",
        "tables",
        "open_FRED-cli",
        "windpowerlib > 0.2.0",
        "pandas >= 1.0",
        "xarray >= 0.12.0",
        "descartes",
        "SQLAlchemy < 1.4.0, >=1.3.0",
    ],
    extras_require={
        "dev": [
            "jupyter",
            "nbformat",
            "punch.py",
            "pytest",
            "sphinx_rtd_theme",
            "open_FRED-cli",
        ],
        "data-sources": ["open_FRED-cli"],
        "examples": ["jupyter", "matplotlib", "descartes"],
    },
)
