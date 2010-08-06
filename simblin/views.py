# -*- coding: utf-8 -*-
"""
    Simblin Views
    ~~~~~~~~~~~~~

    The different views of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from werkzeug import check_password_hash, generate_password_hash
from flask import Module, g, current_app, render_template, session, request, \
    flash, redirect, url_for
from flaskext.sqlalchemy import Pagination

from simblin.extensions import db
from simblin.models import Admin, Entry, Tag
from simblin.helpers import normalize, normalize_tags, convert_markup, \
    login_required
from simblin import signals

view = Module(__name__)


@view.route('/', defaults={'page':1})
@view.route('/<int:page>')
def show_entries(page):
    """Show the latest x blog posts"""
    pagination = Entry.query.order_by(Entry.id.desc()).paginate(page=page, 
        per_page=current_app.config['POSTS_PER_PAGE'])
    if not pagination.total: flash("No entries so far")
    return render_template('entries.html', pagination=pagination,
        endpoint_func=lambda x: url_for('show_entries', page=x))


@view.route('/entry/<slug>')
def show_entry(slug):
    """Show a specific blog post alone"""
    entry = Entry.query.filter_by(slug=slug).first()
    if entry:
        prev_entry = Entry.query.filter_by(id=entry.id-1).first()
        next_entry = Entry.query.filter_by(id=entry.id+1).first()
    if not entry:
        flash("No such entry")
        return redirect(url_for('show_entries'))
    else:
        return render_template('entry.html', entry=entry, prev=prev_entry,
                               next=next_entry)


@view.route('/tag/<tag>', defaults={'page':1})
@view.route('/tag/<tag>/<int:page>')
def show_tag(tag, page):
    """Shows all entries with a specific tag"""
    per_page = current_app.config['POSTS_PER_PAGE']
    entries = Tag.query.filter_by(name=tag).first().entries.order_by(
        Entry.id.desc())
    items = entries.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(entries, page=page, per_page=per_page, 
        total=entries.count(), items=items)
    flash("Posts tagged with '%s'" % tag)
    return render_template('entries.html', pagination=pagination,
        endpoint_func=lambda x: url_for('show_tag', tag=tag, page=x))
        

def preview(args):
    """Returns a preview of a blog post. Use this inside a real view"""
    # Mimic entry object to fill form fields
    entry = dict(
        slug=normalize(args['title']),
        title=args['title'],
        markup=args['markup'],
        html=convert_markup(args['markup']),
        published=datetime.datetime.now(),
        # Mimic the tag relationship field of entry
        tags=[dict(name=tag) for tag in normalize_tags(args['tags'])],
    )
    return render_template('compose.html', entry=entry)


@view.route('/compose', methods=['GET', 'POST'])
@login_required
def add_entry():
    """Create a new blog post"""
    next = request.values.get('next', '')
    error = None
    
    if request.method == 'GET':
        return render_template('compose.html', entry=None)
    
    
    if request.method == 'POST':
        if request.form['action'] == 'Preview':
            return preview(request.form)
        if request.form['action'] == 'Cancel':
            return redirect(next)
        title = request.form['title']
        markup = request.form['markup']
        tags = normalize_tags(request.form['tags'])
        
        if title == '':
            error = 'You must provide a title'
        else:
            entry = Entry(title, markup)
            entry.tags = tags
            db.session.add(entry)
            db.session.commit()
            signals.entry_created.send(entry)
            flash('New entry was successfully posted')
            return redirect(url_for('show_entries'))
    if error: flash(error, 'error')
    return render_template('compose.html')


@view.route('/update/<slug>', methods=['GET', 'POST'])
@login_required
def update_entry(slug):
    """Update a new blog post"""
    next = request.values.get('next', '')
    error = None
    entry = None
    if slug:
        entry = Entry.query.filter_by(slug=slug).first()
        
    if request.method == 'GET':
        if not entry:
            error = 'Invalid slug'
        else:
            return render_template('compose.html', entry=entry)
        
    if request.method == 'POST':
        if request.form['action'] == 'Preview':
            return preview(request.form)
        if request.form['action'] == 'Cancel':
            return redirect(next)
        title = request.form['title']
        markup = request.form['markup']
        tags = normalize_tags(request.form['tags'])
        
        if title == '':
            error = 'You must provide a title'
        elif not entry:
            error = 'Invalid slug'
        else:
            entry.title = title
            entry.markup = markup
            entry.tags = tags
            db.session.commit()
            signals.entry_updated.send(entry)
            flash('Entry was successfully updated')
            return redirect(next or url_for('show_entry', slug=entry.slug))
    if error: flash(error, 'error')
    return redirect(url_for('show_entries'))


@view.route('/delete/<slug>', methods=['GET', 'POST'])
@login_required
def delete_entry(slug):
    next = request.values.get('next', '')
    entry = Entry.query.filter_by(slug=slug).first()
    if not entry:
        flash('No such entry')
        return redirect(next or url_for('show_entries'))
        
    if request.method == 'GET':
        flash("Really delete '%s'?" % entry.title, 'question')
        return render_template('delete.html')
    
    if request.method == 'POST':
        db.session.delete(entry)
        db.session.commit()
        signals.entry_deleted.send(entry)
        flash('Entry deleted')
        # Don't redirect user to a deleted page
        if url_for('show_entry', slug='') in next:
            next = None
        return redirect(next or url_for('show_entries'))


@view.route('/login', methods=['GET', 'POST'])
def login():
    """Log the admin in"""
    # The first visitor shall become the admin
    admin = Admin.query.first()
    if not admin:
        return redirect(url_for('register'))
    
    #: For automatic redirection after login to the last visited page
    next = request.values.get('next', '')
    
    error = None
    if request.method == 'POST':
        if request.form['username'] != admin.username:
            error = 'Invalid username'
        elif not admin.check_password(request.form['password']):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You have been successfully logged in')
            return redirect(next or url_for('show_entries'))
    if error: flash(error, 'error')
    return render_template('login.html')


@view.route('/logout')
def logout():
    """Log the admin out"""
    session.pop('logged_in', None)
    flash('You have been successfully logged out')
    #: For automatic redirection to the last visited page before login
    next = request.values.get('next', '')
    return redirect(next or url_for('show_entries'))


@view.route('/register', methods=['GET', 'POST'])
def register():
    """Register the first visitor of the page. After that don't allow any
    registrations anymore"""
    admin = Admin.query.first()
    if admin:
        flash('There can only be one admin', 'error')
        return redirect(url_for('show_entries'))
    
    if request.method == 'GET':
        return render_template('register.html')
    
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        if username == '':
            error = 'You have to enter a username'
        elif password == '':
            error = 'You have to enter a password'
        elif not password == password2:
            error = "Passwords must match"
        else:
            db.session.add(Admin(username, password))
            db.session.commit()
            session['logged_in'] = True
            flash('You are the new master of this blog')
            return redirect(url_for('add_entry'))
    if error: flash(error, 'error')
    return render_template('register.html')
