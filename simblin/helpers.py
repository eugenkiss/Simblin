# -*- coding: utf-8 -*-
"""
    Simblin Helpers
    ~~~~~~~~~~~~~~~

    Utility functions/classes.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import sqlite3
import unicodedata
import re
import os

from os import urandom
from hashlib import sha512
from contextlib import closing
from functools import wraps
from flask import current_app, g, session, url_for, redirect, request, flash

from simblin.lib import markdown2


def login_required(f):
    """Redirect to login page if user not logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Login required', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def normalize(string):
    """Unify string"""
    string = unicodedata.normalize("NFKD", unicode(string)).encode(
        "ascii", "ignore")
    string = re.sub(r"[^\w]+", " ", string)
    string = "-".join(string.lower().strip().split())
    return string


def normalize_tags(string):
    """Return a list of normalized tags from a string with comma separated
    tags"""
    tags = string.split(',')
    result = []
    for tag in tags:
        normalized = normalize(tag)
        if normalized and not normalized in result: 
            result.append(normalized)
    return result


def convert_markup(string):
    """Convert the argument from markup to html"""
    return markdown2.markdown(string, 
        extras=["code-friendly", "code-color", "footnotes"])
