from setuptools import setup, find_packages

setup(
    name='aether.consumer',
    version='0.0.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    install_requires=[
        "kafka",
        "jsonpath_ng",
        "spavro"
    ],
    packages=find_packages(),
    namespace_packages=['aether']
)
