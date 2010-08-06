# -*- coding: utf-8 -*-
"""
    Simblin
    ~~~~~~~

    Simblin - Simple Blog Engine. A blog engine written with Flask and 
    Sqlalchemy.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from flask import Flask

from simblin.extensions import db
from simblin.views import view


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_pyfile('default-settings.cfg')
    
    # TODO: Add possibility to load real ../settings.cfg and load env variable
    
    # Specially for unit tests
    if config:
        app.config.from_object(config)
    
    db.init_app(app)
        
    app.register_module(view)
    
    return app
