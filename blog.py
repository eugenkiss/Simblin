# -*- coding: utf-8 -*-
"""
    simblin.blog
    ~~~~~~~~~~~~~~

    Simple Blog Engine

    :copyright: (c) 2010 by Eugen Kiss.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""
from __future__ import with_statement
import sqlite3
import datetime
import re
import unicodedata
import markdown2

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from helper import set_password, check_password


app = Flask(__name__)
app.config.from_pyfile('default-settings.cfg')
try:
    app.config.from_pyfile('settings.cfg')
except IOError:
    pass


# Helper

def connect_db():
    # TODO: Explain why Parse_DEcltypes and row factory
    db = sqlite3.connect(app.config['DATABASE'], 
                         detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False, db=None):
    cur = g.db.execute(query, args) if not db else db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


def normalize(string):
    """Give a string a unified form"""
    string = unicodedata.normalize("NFKD", unicode(string)).encode(
        "ascii", "ignore")
    string = re.sub(r"[^\w]+", " ", string)
    string = "-".join(string.lower().strip().split())
    return string


def normalize_tags(string):
    tags = string.split(',')
    result = []
    for tag in tags:
        normalized = normalize(tag)
        if normalized and not normalized in result: 
            result.append(normalized)
    return result


def convert_markdown(string):
    return markdown2.markdown(string)


def get_tags(entry_id):
    """Get a list of all Tags associated with this specific entry"""
    tags = query_db(
        'SELECT * FROM tags, entry_tag '
        'WHERE entry_tag.entry_id=? AND entry_tag.tag_id=tags.id', [entry_id])
    tag_names = [tag['name'] for tag in tags]
    return tag_names


def create_tags(tag_names):
    """Create new unique tags inside the database (if necessary)"""
    for tag_name in tag_names:
        tag = query_db("SELECT * FROM tags WHERE name=? LIMIT 1", 
            [tag_name], one=True)
        # Don't create duplicate tags
        if not tag:
            g.db.execute("INSERT INTO tags (name) VALUES (?)", [tag_name])
    g.db.commit()


def associate_tags(entry_id, tag_names):
    """Inserts new rows in the table that maps tags to entries"""
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
    """Delete all entry-tag associations"""
    g.db.execute("DELETE FROM entry_tag WHERE entry_id=?", [entry_id])
    g.db.commit()

# End Helper


@app.before_request
def before_request():
    g.db = connect_db()


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/')
def show_entries():
    entries = query_db('SELECT * FROM entries ORDER BY id DESC')
    for entry in entries:
        entry['tags'] = get_tags(entry['id'])
    if not entries:
        return redirect(url_for('add_entry'))
    else:
        return render_template('home.html', entries=entries)


@app.route('/entry/<slug>')
def show_entry(slug):
    entry = query_db('SELECT * FROM entries WHERE slug=?', [slug], one=True)
    if not entry:
        flash("No such entry")
        return redirect(url_for('show_entries'))
    else:
        entry['tags'] = get_tags(entry['id'])
        return render_template('entry.html', entry=entry)


@app.route('/compose', methods=['GET', 'POST'])
def add_entry():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # TODO: Use: request.args.get('q', '')
    #       To learn if an id is given. if it is the case, load the specific
    #       entry from the database (if possible) and fill the forms with
    #       its contents.
    #       In the POST request, update the entry instead of inserting another
    #       row.
    error = None
    if request.method == 'GET':
        id = request.args.get('id', '')
        if id:
            entry = query_db('SELECT * FROM entries WHERE id=?', [id], one=True)
            if not entry:
                error = 'Invalid id'
            else:
                tags = get_tags(entry_id=id)
                return render_template('compose.html', entry=entry, tags=tags)
        else:
            return render_template('compose.html', entry=None, tags=None)
    
    # TODO: 
    #       * Create slug (tornado) and normalize and unique it (-2)
    #       
    if request.method == 'POST':
        id = request.form['id']
        title = request.form['title']
        markdown = request.form['markdown']
        # TODO: Make slug unique (see tornado blog)
        slug = normalize(title)
        html = convert_markdown(markdown)
        now = datetime.datetime.now()
        tags = normalize_tags(request.form['tags'])
        create_tags(tags)
        if request.form['title'] == '':
            error = 'You must provide a title'
        elif id and \
            not query_db('SELECT * FROM entries WHERE id=?', [id], one=True):
            error = 'Invalid id'
        else:
            if not id:
                g.db.execute(
                    'INSERT INTO entries ' 
                    '(slug, title, markdown, html, published) ' 
                    'VALUES (?, ?, ?, ?, ?)',
                    [slug, title, markdown, html, now])
                id = query_db('SELECT id FROM entries WHERE slug=?', 
                    [slug], one=True)['id']
                associate_tags(id, tags)
                flash('New entry was successfully posted')
            else:
                g.db.execute(
                    'UPDATE entries SET ' 
                    'slug=?, title=?, markdown=?, html=? ' 
                    'WHERE id=?',
                    [slug, title, markdown, html, id])
                flash('Entry was successfully updated')
                unassociate_tags(id)
                associate_tags(id, tags)
            g.db.commit()
            #return redirect(url_for('show_entry'), slug=slug)
            return redirect(url_for('show_entries'))
    return render_template('compose.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # The first visitor shall become the admin
    admin = query_db('SELECT * FROM admin LIMIT 1', one=True)
    if not admin:
        return redirect(url_for('register'))
    
    error = None
    if request.method == 'POST':
        if request.form['username'] != admin['username']:
            error = 'Invalid username'
        elif not check_password(request.form['password'], admin['password']):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You have been successfully logged in')
            # TODO: Redirect to page the admin was coming from
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been successfully logged out')
    return redirect(url_for('show_entries'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    admin = query_db('SELECT * FROM admin LIMIT 1', one=True)
    if admin:
        # TODO: Redirect to *last* page and show flash error message
        error = 'There can only be one admin'
        return render_template('register.html', error=error)
    if request.method == 'GET':
        return render_template('register.html')
    error = None
    if request.method == 'POST':
        if request.form['username'] == '':
            error = 'You have to enter a username'
        elif request.form['password'] == '':
            error = 'You have to enter a password'
        elif not request.form['password'] == request.form['password2']:
            error = "Passwords must match"
        else:
            g.db.execute('insert into admin (username, password) values (?, ?)',
                [request.form['username'], 
                 set_password(request.form['password'])])
            g.db.commit()
            # TODO: Automatic login after registration
#            app.post(url_for('login'), data=dict(
#                username=request.form['username'],
#                password=request.form['password']))
            flash('You are the new master of this blog')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


if __name__ == '__main__':
    app.run()
