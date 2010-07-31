#!/bin/env python
import sqlite3
#import blog

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


def connect_db():
    from blog import app
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    from blog import app
    from contextlib import closing
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    from blog import g
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv
