#!/bin/env python
from __future__ import with_statement
import sqlite3
import datetime
import settings

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from helper import set_password, check_password


app = Flask(__name__)
app.config.from_object(settings)


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


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

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
    entries = query_db('select * from entries order by id desc')
    if not entries:
        return redirect(url_for('add_entry'))
    else:
        return render_template('home.html', entries=entries)


@app.route('/entry/<slug>')
def show_entry(slug):
    return "TODO"


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
    if request.method == 'GET':
        # TODO: Add id argument to be able to edit specific post
        return render_template('compose.html')
    if request.method == 'POST':
        # TODO: * Convert markdown to html here
        #       * Create slug (tornado) and normalize and unique it (-2)
        #       * Normalize tagss
        g.db.execute(
            'insert into entries (slug, title, markdown, html, published)' 
            'values (?, ?, ?, ?, ?)',
                     [request.form['title'],
                      request.form['title'], 
                      request.form['markdown'],
                      request.form['markdown'],
                      datetime.datetime.now()])
        g.db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))


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
