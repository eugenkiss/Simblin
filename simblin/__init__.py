# -*- coding: utf-8 -*-
"""
    simblin
    ~~~~~~~~~~~~~~

    Simblin - Simple Blog Engine

    :copyright: (c) 2010 by Eugen Kiss.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""
from flask import Flask, g

from views import view
from helpers import connect_db


def create_app(config=None):
    app = Flask(__name__)
    
    app.config.from_pyfile('default-settings.cfg')
    
    if config:
        app.config.from_object(config)
        
    @app.before_request
    def before_request():
        g.db = connect_db(app.config['DATABASE'])

    @app.after_request
    def after_request(response):
        g.db.close()
        return response

    app.register_module(view)
    
    return app
