import os
from setuptools import setup, find_packages
import sys

if sys.version_info < (3,0):
    sys.exit('aether data mocker requires Python 3.x')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='aether.mocker',
    version='0.0.0',
    install_requires=[
        "aether-client"
    ],
    packages=find_packages(),
    namespace_packages=['aether']
)
