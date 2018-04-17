#!/usr/bin/python3

from setuptools import setup

setup(
    name='aether.kafka',
    version='0.0.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        "kafka",
        "jsonpath_ng"
    ],
    packages=find_packages(),
    namespace_packages=['aether']
)
