import os
from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='aether.client',
    version='0.0.0',
    install_requires=[
        "requests"
    ],
    packages=find_packages(),
    namespace_packages=['aether']
)
