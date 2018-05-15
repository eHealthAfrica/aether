from setuptools import setup
setup(
    name='myconsumer',
    author='Shawn Sarwar',
    author_email="shawn.sarwar@ehealthafrica.org",
    decription='''A aether consumer for sqlalchemy''',
    version='1.0.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'sqlalchemy', 'alembic', 'aether.consumer'],
    url='http://github.com/eHealthAfrica/aether',
    keywords=['aether', 'kafka', 'consumer'],
    classifiers=[]
)
