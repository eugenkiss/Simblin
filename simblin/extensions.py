# -*- coding: utf-8 -*-
"""
    Simblin Extensions
    ~~~~~~~~~~~~~~~~~~

    Various extensions.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from flaskext.sqlalchemy import SQLAlchemy

__all__ = ['db']

db = SQLAlchemy()
