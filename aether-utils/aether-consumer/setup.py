from setuptools import setup, find_packages

setup(
    name='aether.consumer',
    author='Shawn Sarwar',
    author_email="shawn.sarwar@ehealthafrica.org",
    decription='''A library to consume messages from Kafka with added functionality based on
        Aether's schema metadata''',
    version='1.0.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'mock'],
    url='http://github.com/eHealthAfrica/aether',
    install_requires=[
        "kafka",
        "jsonpath_ng",
        "spavro"
    ],
    packages=find_packages(),
    namespace_packages=['aether'],
    keywords=['aether', 'kafka', 'consumer'],
    classifiers=[]
)
