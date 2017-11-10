from setuptools import setup


version = __import__('edw.djutils', fromlist=['__version__']).__version__

setup(
    name='edw.djutils',
    version=version,
    url='https://github.com/eaudeweb/edw.djutils',
    license='Apache',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    packages=['edw.djutils'],
    # this is unnecessary, because Python3-only
    #namespace_packages=['edw'],
)
