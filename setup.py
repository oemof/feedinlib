import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="feedinlib",
    version="0.1.0rc4",
    description="Creating time series from pv or wind power plants.",
    url="http://github.com/oemof/feedinlib",
    author="oemof developer group",
    author_email="windpowerlib@rl-institut.de",
    license="MIT",
    packages=["feedinlib"],
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    zip_safe=False,
    install_requires=[
        "cdsapi >= 0.1.4",
        "geopandas",
        "numpy >= 1.7.0",
        "oedialect >= 0.0.6.dev0",
        "open_FRED-cli",
        "pandas >= 0.13.1",
        "pvlib >= 0.7.0",
        "tables",
        "windpowerlib >= 0.2.0",
        "xarray >= 0.12.0",
        "descartes"
    ],
    extras_require={
        "dev": [
            "jupyter",
            "nbformat",
            "punch.py",
            "pytest",
            "sphinx_rtd_theme",
        ],
        "examples": ["jupyter",
                     "matplotlib",
                     "descartes"],
    },
)
