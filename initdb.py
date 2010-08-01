import os
from simblin.helpers import init_db
from simblin import create_app

app = create_app()

init_db(os.path.join('simblin', app.config['DATABASE']))

print "Initialized new empty database"
