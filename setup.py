# -*- coding: utf-8 -*-
"""
@author: uwe
"""

import sys
import os
from setuptools import setup

setup(name='feedinlib',
      version='0.0.10',
      description='Creating time series from pv or wind power plants.',
      url='http://github.com/oemof/feedinlib',
      author='oemof developing group',
      author_email='mail',
      license='GPL3',
      packages=['feedinlib'],
      zip_safe=False,
      install_requires=['numpy >= 1.7.0',
                        'pandas >= 0.13.1',
                        'pvlib >= 0.4.0',
                        'windpowerlib',
                        'requests'])
