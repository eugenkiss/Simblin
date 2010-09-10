import os

BLOG_TITLE = 'Simblin'
POSTS_PER_PAGE = 5
SECRET_KEY = 'abc'
# Put the database in the simblin folder
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s/simblin.db' % os.path.dirname(__file__)
SQLALCHEMY_ECHO = False
DEBUG = True
PORT = 5000
DISQUS_SHORTNAME = ''

# For Feed
AUTHOR = "Batman"
BLOG_URL = "http://blog.batcave.net"
