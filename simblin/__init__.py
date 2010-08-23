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

import default_settings


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(default_settings)
    
    app.config.from_envvar('SIMBLIN_SETTINGS', silent=True)
    
    if config:
        app.config.from_object(config)
    
    db.init_app(app)
        
    app.register_module(admin)
    app.register_module(main)
    
    return app
