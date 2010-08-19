from __future__ import with_statement
import os
from simblin.extensions import db
from simblin import create_app

app = create_app()

with app.test_request_context():
    # The context is needed so db can access the configuration of the app
    db.create_all()

print "Initialized new empty database"
