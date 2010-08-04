# -*- coding: utf-8 -*-
from __future__ import with_statement
import sqlite3
import unicodedata
import re
import datetime
import markdown2
import os

from os import urandom
from hashlib import sha512
from contextlib import closing
from functools import wraps

from flask import current_app, g, session, url_for, redirect, request, flash


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


def convert_markdown(string):
    """Convert the argument from markdown to html"""
    return markdown2.markdown(string, 
        extras=["code-friendly", "code-color", "footnotes"])


def connect_db(db_path):
    """Open a connection to a database"""
    # TODO: Explain why Parse_DEcltypes and row factory
    db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db


def init_db(db_path):
    """Create the database tables."""
    with closing(connect_db(db_path)) as db:
        with current_app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    """Simplify interfacing with sqlite3"""
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def get_tags(entry_id):
    """Get a list of all Tags associated with a specific entry"""
    tags = query_db(
        'SELECT * FROM tags, entry_tag '
        'WHERE entry_tag.entry_id=? AND entry_tag.tag_id=tags.id', 
        [entry_id])
    tag_names = [tag['name'] for tag in tags]
    return tag_names


def create_tags(tag_names):
    """Create new, *unique* tags inside the database"""
    for tag_name in tag_names:
        tag = query_db("SELECT * FROM tags WHERE name=? LIMIT 1", 
            [tag_name], one=True)
        # Don't create duplicate tags
        if not tag:
            g.db.execute("INSERT INTO tags (name) VALUES (?)", [tag_name])
    g.db.commit()
    

def tidy_tags():
    """Delete tags that are not associated to at least one entry"""
    associated_tag_ids = query_db('SELECT tag_id FROM entry_tag')
    associated_tag_ids = [x['tag_id'] for x in associated_tag_ids]
    tags = query_db('SELECT id FROM tags')
    for tag in tags:
        if tag['id'] not in associated_tag_ids:
            g.db.execute('DELETE FROM tags WHERE id=?', [tag['id']])
    g.db.commit()
    

def associate_tags(entry_id, tag_names):
    """Create new associations between tags and a specific entry"""
    for tag_name in tag_names:
        tag = query_db("SELECT * FROM tags WHERE name=? LIMIT 1", 
            [tag_name], one=True)
        # Only associate existing tags
        if tag:
            g.db.execute(
                "INSERT INTO entry_tag (entry_id, tag_id) VALUES (?, ?)", 
                [entry_id, tag['id']])
    g.db.commit()
    
    
def unassociate_tags(entry_id):
    """Delete all tag associations of a specific entry"""
    g.db.execute("DELETE FROM entry_tag WHERE entry_id=?", [entry_id])
    g.db.commit()
