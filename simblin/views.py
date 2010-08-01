# -*- coding: utf-8 -*-
import datetime

from flask import Module, g, current_app, render_template, session, request, \
    flash, redirect, url_for

from helpers import set_password, check_password, normalize, normalize_tags, \
    convert_markdown, connect_db, init_db, query_db, get_tags, create_tags, \
    associate_tags, unassociate_tags

view = Module(__name__)


@view.route('/')
def show_entries():
    entries = query_db('SELECT * FROM entries ORDER BY id DESC')
    for entry in entries:
        entry['tags'] = get_tags(entry['id'])
    if not entries:
        return redirect(url_for('add_entry'))
    else:
        return render_template('home.html', entries=entries)


@view.route('/entry/<slug>')
def show_entry(slug):
    entry = query_db('SELECT * FROM entries WHERE slug=?', [slug], one=True)
    if not entry:
        flash("No such entry")
        return redirect(url_for('show_entries'))
    else:
        entry['tags'] = get_tags(entry['id'])
        return render_template('entry.html', entry=entry)


@view.route('/compose', methods=['GET', 'POST'])
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


@view.route('/login', methods=['GET', 'POST'])
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


@view.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been successfully logged out')
    return redirect(url_for('show_entries'))


@view.route('/register', methods=['GET', 'POST'])
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
