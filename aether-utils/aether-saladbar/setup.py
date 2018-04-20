import os
from setuptools import setup, find_packages
import sys

if sys.version_info > (3,0):
    sys.exit('saladbar requires Python 2.x for schema_salad_tool')

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='aether-saladbar',
    version='0.0.0',
    install_requires=[
	"schema-salad"
    ],
    include_package_data=True,
    packages=find_packages(),
)
