# -*- coding: utf-8 -*-
"""
    Simblin Admin Views
    ~~~~~~~~~~~~~~~~~~~

    The different views of the blogging application that are meant for the
    admin.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from flask import Module, render_template, session, request, \
                  flash, redirect, url_for, jsonify, abort

from simblin import signals
from simblin.extensions import db
from simblin.models import Admin, Post, Category
from simblin.helpers import normalize_tags, convert_markup, login_required, \
                            normalize


admin = Module(__name__)


@admin.route('/does-not-exist')
def disqus():
    """Specifically needed for disqus"""
    abort(404)


@admin.route('/compose', methods=['GET', 'POST'], defaults={'slug':None})
@admin.route('/update/<slug>', methods=['GET', 'POST'])
@login_required
def create_post(slug):
    """Create a new or edit an existing blog post"""
    next = request.values.get('next', '')
    post = None
    if slug:
        post = Post.query.filter_by(slug=slug).first()
    if slug and not post:
        flash('Invalid slug', 'error')
        return redirect(next)
    
    if request.method == 'GET':
        return render_template('admin/compose.html', post=post,
            categories=Category.query.all())
            
    if request.method == 'POST':
        if request.form['action'] == 'Cancel':
            return redirect(next)
        
        title = request.form['title']
        markup = request.form['markup']
        tags = normalize_tags(request.form['tags'])
        comments_allowed = bool(request.values.get('comments_allowed', False))
        visible = bool(request.values.get('visible', False))
        #: Contains the ids of the categories
        categories = []
        for name, id in request.form.iteritems():
            if 'category-' in name:
                categories.append(id)
                
        if title == '':
            flash('You must provide a title', 'error')
            return render_template('admin/compose.html')
        elif request.form['action'] == 'Publish':
            post = Post(title, markup, comments_allowed, visible)
            post.tags = tags
            post.categories = categories
            db.session.add(post)
            db.session.commit()
            signals.post_created.send(post)
            flash('New post was successfully posted')
            return redirect(url_for('main.show_posts'))
        elif request.form['action'] == 'Update':
            post.title = title
            post.markup = markup
            post.comments_allowed = comments_allowed
            post.visible = visible
            post.tags = tags
            post.categories = categories
            db.session.commit()
            signals.post_updated.send(post)
            flash('Post was successfully updated')
            return redirect(url_for('main.show_post', slug=post.slug))
        

@admin.route('/_delete/<slug>', methods=['GET', 'POST'])
@login_required
def delete_post(slug):
    """Delete a post if existent. Ought to be used with an ajax request"""
    next = request.values.get('next', '')
    post = Post.query.filter_by(slug=slug).first()
    if not post:
        flash('No such post')
        return redirect(next or url_for('main.show_posts'))
    
    if request.method == 'POST':
        db.session.delete(post)
        db.session.commit()
        signals.post_deleted.send(post)
        flash('Post deleted')
        # Don't redirect user to a deleted page
        if url_for('main.show_post', slug='') in next:
            next = None
        return redirect(next or url_for('main.show_posts'))


@admin.route('/_add_category', methods=['POST'])
@login_required
def add_category():
    """Add category to database and return its id"""
    category = Category(request.form['name'])
    db.session.add(category)
    db.session.commit()
    return jsonify(id=category.id, name=category.name,
        url=url_for('main.show_category', category=category.name))
        
        
@admin.route('/_delete_category', methods=['POST'])
@login_required
def delete_category():
    """Delete category specified by id from database"""
    category = Category.query.get(request.form['id'])
    db.session.delete(category)
    db.session.commit()
    return ''


@admin.route('/_preview', methods=['POST'])
@login_required
def preview():
    """Returns a preview of a blog post. Use with an Ajax request"""
    args = request.form
    # Mimic post object
    post = dict(
        slug=normalize(args['title']), 
        title=args['title'],
        markup=args['markup'],
        visible=True,
        html=convert_markup(args['markup']),
        datetime=datetime.datetime.fromtimestamp(int(args['datetime'])),
        # Mimic the tag relationship field of post
        tags=[dict(name=tag) for tag in normalize_tags(args['tags'])],
        # Mimic the category relationship field of post
        categories=[dict(name=name) for name in 
            filter(lambda x: x != '', set(args['categories'].split(',')))],
    )
    return render_template('admin/_preview.html', post=post)


@admin.route('/login', methods=['GET', 'POST'])
def login():
    """Log the admin in"""
    # The first visitor shall become the admin
    admin = Admin.query.first()
    if not admin:
        return redirect(url_for('admin.register'))
    
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
            return redirect(next or url_for('main.show_posts'))
    if error: flash(error, 'error')
    return render_template('admin/login.html')


@admin.route('/logout')
def logout():
    """Log the admin out"""
    session.pop('logged_in', None)
    flash('You have been successfully logged out')
    #: For automatic redirection to the last visited page before login
    next = request.values.get('next', '')
    return redirect(next or url_for('main.show_posts'))


@admin.route('/register', methods=['GET', 'POST'])
def register():
    """Register the first visitor of the page as the admin. The admin can
    'reregister' to change his/her password, email etc."""
    admin = Admin.query.first()
    if admin:
        if not session.get('logged_in'):
            flash('There can only be one admin', 'error')
            return redirect(url_for('main.show_posts'))
        # Reregister
        db.session.delete(admin)
        db.session.commit()
        flash('Reregister with your new credentials')
        return redirect(url_for('admin.register'))
    
    if request.method == 'GET':
        return render_template('admin/register.html')
    
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        if username == '':
            error = 'You have to enter a username'
        elif password == '':
            error = 'You have to enter a password'
        elif not password == password2:
            error = "Passwords must match"
        else:
            db.session.add(Admin(username, email, password))
            db.session.commit()
            session['logged_in'] = True
            flash('You are the new master of this blog')
            return redirect(url_for('create_post'))
    if error: flash(error, 'error')
    return render_template('admin/register.html')
