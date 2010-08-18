import sys 
import os 
import site 
 
sys.stdin = sys.stdout 
 
site.addsitedir("/var/www/blog/env/lib/python2.5/site-packages") 
 
BASE_DIR = os.path.join(os.path.dirname(__file__)) 
sys.path.append(BASE_DIR) 

import settings
 
from simblin import create_app 
 
application = create_app(settings) 
