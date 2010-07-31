#!/bin/env python
from __future__ import with_statement
import sqlite3
import settings

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from helper import set_password, check_password, connect_db, query_db


app = Flask(__name__)
app.config.from_object(settings)


@app.before_request
def before_request():
    g.db = connect_db()


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route('/')
def show_entries():
    entries = query_db('select title, html from entries order by id desc')
    if not entries:
        return redirect(url_for('add_entry'))
    else:
        return render_template('show_entries.html', entries=entries)


@app.route('/entry/<slug>')
def show_entry(slug):
    return "TODO"


@app.route('/compose', methods=['GET', 'POST'])
def add_entry():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'GET':
        # TODO: Add id argument to be able to edit specific post
        return render_template('compose.html')
    if request.method == 'POST':
        # TODO: Convert markdown to html here
        g.db.execute('insert into entries (title, html) values (?, ?)',
                     [request.form['title'], request.form['markdown']])
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
            flash('You were successfully logged in')
            # TODO: Redirect to page the admin was coming from
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    # There can only be one ...admin!
    admin = query_db('SELECT * FROM admin LIMIT 1', one=True)
    if admin:
        # TODO: Redirect to last page and show flash error message
        return 'There can only be one...'
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        g.db.execute('insert into admin (username, password) values (?, ?)',
            [request.form['username'], set_password(request.form['password'])])
        g.db.commit()
        flash('You are the new master of this blog')
        # TODO: Automatically login
        return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run()
