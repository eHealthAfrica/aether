import os
from setuptools import setup, find_packages
import sys

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='aether.saladbar',
    version='0.0.0',
    install_requires=[
	"schema-salad"
    ],
    include_package_data=True,
    packages=find_packages(),
    namespace_packages=['aether']
)
