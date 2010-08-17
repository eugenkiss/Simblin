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
from simblin.views.admin import admin
from simblin.views.main import main


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_pyfile('default-settings.cfg')
    
    try:    
        app.config.from_pyfile('../settings.cfg')
    except IOError:
        pass
    
    app.config.from_envvar('SIMBLIN_SETTINGS', silent=True)
    
    # Specially for unit tests
    if config:
        app.config.from_object(config)
    
    db.init_app(app)
        
    app.register_module(admin)
    app.register_module(main)
    
    return app
