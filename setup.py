import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='feedinlib',
      version='0.1.0dev',
      description='Creating time series from pv or wind power plants.',
      url='http://github.com/oemof/feedinlib',
      author='oemof developer group',
      author_email='windpowerlib@rl-institut.de',
      license='MIT',
      packages=['feedinlib'],
      long_description=read('README.rst'),
      long_description_content_type='text/x-rst',
      zip_safe=False,
      install_requires=['pandas',
                        'pvlib >= 0.6.0',
                        'windpowerlib >= 0.2.0'],
      extras_require={
          'dev': ['pytest', 'jupyter', 'sphinx_rtd_theme', 'nbformat'],
          'examples': ['jupyter']}
)
