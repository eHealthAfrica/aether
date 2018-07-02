from setuptools import setup
setup(
    name='aether-sdk-example',
    author='Shawn Sarwar',
    author_email="shawn.sarwar@ehealthafrica.org",
    decription='''An SDK demo implementing a simple command line Kafka topic viewer''',
    version='1.0.0',
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'sqlalchemy', 'alembic', 'aet.consumer'],
    url='http://github.com/eHealthAfrica/aether',
    keywords=['aet', 'aether', 'kafka', 'consumer'],
    classifiers=[]
)
