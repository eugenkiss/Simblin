# -*- coding: utf-8 -*-
"""
    Simblin Views
    ~~~~~~~~~~~~~

    The different views of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from flask import Module, current_app, render_template, session, request, \
                  flash, redirect, url_for, jsonify
from flaskext.sqlalchemy import Pagination

from simblin import signals
from simblin.extensions import db
from simblin.models import Admin, Post, Tag
from simblin.helpers import normalize_tags, convert_markup, login_required, \
                            normalize


view = Module(__name__)


@view.route('/', defaults={'page':1})
@view.route('/<int:page>')
def show_posts(page):
    """Show the latest x blog posts"""
    pagination = Post.query.order_by(Post.id.desc()).paginate(page=page, 
        per_page=current_app.config['POSTS_PER_PAGE'])
    if not pagination.total: flash("No posts so far")
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('show_posts', page=x))


@view.route('/post/<slug>')
def show_post(slug):
    """Show a specific blog post alone"""
    post = Post.query.filter_by(slug=slug).first()
    if post:
        prev_post = Post.query.filter_by(id=post.id-1).first()
        next_post = Post.query.filter_by(id=post.id+1).first()
    if not post:
        flash("No such post")
        return redirect(url_for('show_posts'))
    else:
        return render_template('post.html', post=post, prev=prev_post,
                               next=next_post)


@view.route('/tag/<tag>', defaults={'page':1})
@view.route('/tag/<tag>/<int:page>')
def show_tag(tag, page):
    """Shows all posts with a specific tag"""
    per_page = current_app.config['POSTS_PER_PAGE']
    posts = Tag.query.filter_by(name=tag).first().posts.order_by(
        Post.id.desc())
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Posts tagged with '%s'" % tag)
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('show_tag', tag=tag, page=x))
        

@view.route('/_preview', methods=['POST'])
def preview():
    """Returns a preview of a blog post. Used with an Ajax request"""
    args = request.form
    print request.form
    # Mimic post object
    post = dict(
        slug=normalize(args['title']), 
        title=args['title'],
        markup=args['markup'],
        html=convert_markup(args['markup']),
        published=datetime.datetime.now(),
        # Mimic the tag relationship field of post
        tags=[dict(name=tag) for tag in normalize_tags(args['tags'])],
    )
    return render_template('_preview.html', post=post)


@view.route('/compose', methods=['GET', 'POST'], defaults={'slug':None})
@view.route('/update/<slug>', methods=['GET', 'POST'])
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
        return render_template('compose.html', post=post)
            
    if request.method == 'POST':
        if request.form['action'] == 'Cancel':
            return redirect(next)
        
        title = request.form['title']
        markup = request.form['markup']
        tags = normalize_tags(request.form['tags'])
        if title == '':
            flash('You must provide a title', 'error')
            return render_template('compose.html')
        elif request.form['action'] == 'Publish':
            post = Post(title, markup)
            post.tags = tags
            db.session.add(post)
            db.session.commit()
            signals.post_created.send(post)
            flash('New post was successfully posted')
            return redirect(url_for('show_posts'))
        elif request.form['action'] == 'Update':
            post.title = title
            post.markup = markup
            post.tags = tags
            db.session.commit()
            signals.post_updated.send(post)
            flash('Post was successfully updated')
            return redirect(next or url_for('show_post', slug=post.slug))


@view.route('/delete/<slug>', methods=['GET', 'POST'])
@login_required
def delete_post(slug):
    next = request.values.get('next', '')
    post = Post.query.filter_by(slug=slug).first()
    if not post:
        flash('No such post')
        return redirect(next or url_for('show_posts'))
        
    if request.method == 'GET':
        flash("Really delete '%s'?" % post.title, 'question')
        return render_template('delete.html')
    
    if request.method == 'POST':
        db.session.delete(post)
        db.session.commit()
        signals.post_deleted.send(post)
        flash('Post deleted')
        # Don't redirect user to a deleted page
        if url_for('show_post', slug='') in next:
            next = None
        return redirect(next or url_for('show_posts'))


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
            return redirect(next or url_for('show_posts'))
    if error: flash(error, 'error')
    return render_template('login.html')


@view.route('/logout')
def logout():
    """Log the admin out"""
    session.pop('logged_in', None)
    flash('You have been successfully logged out')
    #: For automatic redirection to the last visited page before login
    next = request.values.get('next', '')
    return redirect(next or url_for('show_posts'))


@view.route('/register', methods=['GET', 'POST'])
def register():
    """Register the first visitor of the page. After that don't allow any
    registrations anymore"""
    admin = Admin.query.first()
    if admin:
        flash('There can only be one admin', 'error')
        return redirect(url_for('show_posts'))
    
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
            return redirect(url_for('create_post'))
    if error: flash(error, 'error')
    return render_template('register.html')
