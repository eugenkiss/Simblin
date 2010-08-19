# -*- coding: utf-8 -*-
"""
    setup.py
    ~~~~~~~~

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from setuptools import setup

setup(
    name='simblin',
    version='0.1',
    packages=['simblin'],
    zip_safe=False,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'blinker',
        'Pygments',
    ],
    include_package_data=True,
)
