#!/bin/env python
import sqlite3

from os import urandom
from hashlib import sha512


def set_password(raw_password):
    """Returns a secure representation of a password"""
    salt = sha512(urandom(8)).hexdigest()
    hsh = sha512('%s%s' % (salt, raw_password)).hexdigest()
    return '%s$%s' % (salt, hsh)


def check_password(raw_password, enc_password):
    """Returns a boolean of whether the raw_password was correct"""
    salt, hsh = enc_password.split('$')
    return hsh == sha512('%s%s' % (salt, raw_password)).hexdigest()

# TODO: put connect_db, init_db and query_db here
#       Maybe refactoring as package helps with circular imports?


