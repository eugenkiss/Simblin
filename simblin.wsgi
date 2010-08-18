from simblin import create_app

activate_this = '/var/www/blog/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

application = create_app()
