from setuptools import setup, find_packages


version = __import__('edw.djutils', fromlist=['__version__']).__version__

setup(
    name='edw.djutils',
    version=version,
    url='https://github.com/eaudeweb/edw.djutils',
    license='Apache',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    packages=[
        'edw.djutils'
    ] + [
        'edw.djutils.%s' % package
        for package in find_packages('edw/djutils')
    ],
    # this is unnecessary, because Python3-only
    #namespace_packages=['edw'],
    # must not be zipped, or it won't work as a namespace package
    zip_safe=False,
)
