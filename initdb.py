import os
from simblin.extensions import db
from simblin import create_app

app = create_app()

# TODO: Explain why the need for request context
with app.test_request_context():
    db.create_all()

print "Initialized new empty database"
