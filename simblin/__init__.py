# -*- coding: utf-8 -*-
"""
    Simblin
    ~~~~~~~

    Simblin - Simple Blog Engine. A blog engine written with Flask and Sqlite3.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from flask import Flask
from extensions import db
from views import view


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_pyfile('default-settings.cfg')
    if config:
        app.config.from_object(config)
    
    db.init_app(app)
        
    app.register_module(view)
    
    return app
