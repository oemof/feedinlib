# -*- coding: utf-8 -*-
"""
@author: uwe
"""

import sys
import os
from setuptools import setup

# check python version.
if not sys.version_info[:2] in ((2, 7), (3, 3), (3, 4)):
    sys.exit('%s requires Python 2.7, 3.3, or 3.4' % 'feedinlib')

setup(name='feedinlib',
      version='0.0.6',
      description='Creating time series from pv or wind power plants.',
      url='http://github.com/oemof/feedinlib',
      author='oemof developing group',
      author_email='mail',
      license='GPL3',
      packages=['feedinlib'],
      zip_safe=False,
      install_requires=['numpy >= 1.7.0',
                        'pandas >= 0.13.1',
                        'pvlib >= 0.2.1',
                        'urllib5'])
