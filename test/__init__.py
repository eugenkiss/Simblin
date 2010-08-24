# -*- coding: utf-8 -*-
"""
    Simblin Tests Init
    ~~~~~~~~~~~~~~~~~~

    Initialize the app and the database for the tests and provide common
    functions.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from flaskext.testing import TestCase as _TestCase

from simblin import create_app
from simblin.extensions import db


class TestCase(_TestCase):
    """Base TestClass for application."""
    
    TESTING = True
    CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ECHO = False
    
    def create_app(self):
        return create_app(self)
    
    def clear_db(self):
        db.drop_all()
        db.create_all()
    
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self._ctx.push() # Why do I need this line?
        db.drop_all()
