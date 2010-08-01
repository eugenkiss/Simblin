from simblin import create_app
# TODO: if settings.cfg is inside this directory load it otherwise load
#       default settings
app = create_app()
app.run()
