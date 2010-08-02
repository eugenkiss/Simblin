# -*- coding: utf-8 -*-
"""
    Simblin Views
    ~~~~~~~~~~~~~

    The different views of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from flask import Module, g, current_app, render_template, session, request, \
    flash, redirect, url_for

from helpers import set_password, check_password, normalize, normalize_tags, \
    convert_markdown, connect_db, init_db, query_db, get_tags, create_tags, \
    associate_tags, unassociate_tags, tidy_tags, login_required

view = Module(__name__)


@view.route('/')
def show_entries():
    """Show the latest x blog posts"""
    entries = query_db('SELECT * FROM entries ORDER BY id DESC')
    for entry in entries:
        entry['tags'] = get_tags(entry['id'])
    if not entries:
        return redirect(url_for('add_entry'))
    else:
        return render_template('home.html', entries=entries)


@view.route('/entry/<slug>')
def show_entry(slug):
    """Show a specific blog post alone"""
    entry = query_db('SELECT * FROM entries WHERE slug=?', [slug], one=True)
    if not entry:
        flash("No such entry")
        return redirect(url_for('show_entries'))
    else:
        entry['tags'] = get_tags(entry['id'])
        return render_template('entry.html', entry=entry)


@view.route('/compose', methods=['GET', 'POST'])
@login_required
def add_entry():
    """Create a new blog post"""
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
        
    if request.method == 'POST':
        id = request.form['id']
        title = request.form['title']
        markdown = request.form['markdown']
        slug = normalize(title)
        # In order to make slug unique
        while True:
            entry = query_db('SELECT * FROM entries WHERE slug=?', [slug],
                one=True)
            if not entry: break
            slug += "-2"
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
                # Create new entry
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
                # Update existing entry
                g.db.execute(
                    'UPDATE entries SET ' 
                    'slug=?, title=?, markdown=?, html=? ' 
                    'WHERE id=?',
                    [slug, title, markdown, html, id])
                flash('Entry was successfully updated')
                unassociate_tags(id)
                associate_tags(id, tags)
            tidy_tags()
            g.db.commit()
            return redirect(url_for('show_entries'))
    if error: flash(error, 'error')
    return render_template('compose.html')


@view.route('/login', methods=['GET', 'POST'])
def login():
    """Log the admin in"""
    # The first visitor shall become the admin
    admin = query_db('SELECT * FROM admin LIMIT 1', one=True)
    if not admin:
        return redirect(url_for('register'))
    
    #: For automatic redirection to the last visited page before login
    next = request.values.get('next', '')
    
    error = None
    if request.method == 'POST':
        if request.form['username'] != admin['username']:
            error = 'Invalid username'
        elif not check_password(request.form['password'], admin['password']):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You have been successfully logged in')
            return redirect(next if next else url_for('show_entries'))
    if error: flash(error, 'error')
    return render_template('login.html')


@view.route('/logout')
def logout():
    """Log the admin out"""
    session.pop('logged_in', None)
    flash('You have been successfully logged out')
    #: For automatic redirection to the last visited page before login
    next = request.values.get('next', '')
    return redirect(next if next else url_for('show_entries'))


@view.route('/register', methods=['GET', 'POST'])
def register():
    """Register the first visitor of the page. After that don't allow any
    registrations anymore"""
    admin = query_db('SELECT * FROM admin LIMIT 1', one=True)
    if admin:
        flash('There can only be one admin', 'error')
        return redirect(url_for('show_entries'))
    
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
            session['logged_in'] = True
            flash('You are the new master of this blog')
            return redirect(url_for('login'))
    if error: flash(error, 'error')
    return render_template('register.html')
