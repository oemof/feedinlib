# -*- coding: utf-8 -*-
"""
@author: uwe
"""

import sys
import os
from setuptools import setup

setup(name='feedinlib',
      version='0.0.12',
      description='Creating time series of pv or wind power plants.',
      url='http://github.com/oemof/feedinlib',
      author='oemof developing group',
      author_email='birgit.schachler@rl-institut.de',
      license='GPL3',
      packages=['feedinlib'],
      zip_safe=False,
      install_requires=['numpy >= 1.7.0',
                        'pandas >= 0.13.1',
                        'scipy'],
      extras_require={
          'PVlib': ['pvlib >= 0.5.0'],
          'Windpowerlib': ['windpowerlib >= 0.1.0'],
      })
