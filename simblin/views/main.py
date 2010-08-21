# -*- coding: utf-8 -*-
"""
    Simblin Main Views
    ~~~~~~~~~~~~~~~~~~

    The different views of the blogging application that are accessible by every
    visitor.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from flask import Module, current_app, render_template, session, request, \
                  flash, redirect, url_for, jsonify
from flaskext.sqlalchemy import Pagination

from simblin import signals
from simblin.extensions import db
from simblin.models import Admin, Post, Tag, Category
from simblin.helpers import normalize_tags, convert_markup, login_required, \
                            normalize


main = Module(__name__)


@main.route('/', defaults={'page':1})
@main.route('/<int:page>')
def show_posts(page):
    """Show the latest x blog posts"""
    pagination = Post.query.order_by(Post.id.desc()).paginate(page=page, 
        per_page=current_app.config['POSTS_PER_PAGE'])
    if not pagination.total: flash("No posts so far")
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_posts', page=x))
        
        
@main.route('/post/<slug>')
def show_post(slug):
    """Show a specific blog post alone"""
    post = Post.query.filter_by(slug=slug).first()
    if post:
        prev_post = Post.query.filter_by(id=post.id-1).first()
        next_post = Post.query.filter_by(id=post.id+1).first()
    if not post:
        flash("No such post")
        return redirect(url_for('main.show_posts'))
    else:
        return render_template('post.html', post=post, prev=prev_post,
                               next=next_post)
        

@main.route('/tag/<tag>/', defaults={'page':1})
@main.route('/tag/<tag>/<int:page>/')
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
        endpoint_func=lambda x: url_for('main.show_tag', tag=tag, page=x))
        
        
@main.route('/category/<category>/', defaults={'page':1})
@main.route('/category/<category>/<int:page>/')
def show_category(category, page):
    """Shows all posts in a category"""
    # TODO: Add a test for this
    if not Category.query.filter_by(name=category).first():
        flash("No such category '%s'" % category)
        return redirect(url_for('main.show_posts'))
    per_page = current_app.config['POSTS_PER_PAGE']
    posts = Category.query.filter_by(name=category).first().posts
    posts = posts.order_by(Post.id.desc())
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Posts in category '%s'" % category)
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_category', category=category, 
                                        page=x))
                                        
                                        
@main.route('/uncategorized/', defaults={'page':1})
@main.route('/uncategorized/<int:page>/')
def show_uncategorized(page):
    """Shows all posts which aren't in any category"""
    per_page = current_app.config['POSTS_PER_PAGE']
    posts = Post.query.filter(Post.categories==None)
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Uncategorized posts")
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_uncategorized', page=x))
        
        
# TODO: Test month view
@main.route('/<int:year>/<int:month>/', defaults={'page':1})
@main.route('/<int:year>/<int:month>/<int:page>/')
def show_month(year, month, page):
    """Show all posts from a specific year and month"""
    from calendar import month_name
    per_page = current_app.config['POSTS_PER_PAGE']
    posts = Post.query.filter(db.extract('year', Post.datetime)==year)
    posts = posts.filter(db.extract('month', Post.datetime)==month)
    posts = posts.order_by(Post.id.desc()) 
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Posts from %s %d" % (month_name[month], year))
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_month', year=year, month=month, 
        page=x))
        
        
@main.route('/archives/')
def show_archives():
    """Show the archive. That is recent posts, posts by category etc."""
    latest = Post.query.order_by(Post.id.desc()).limit(5)
    months = Post.query.get_months()
    tags = Tag.query.all()
    #: Needed for calculation of tag cloud
    max_count = Tag.query.get_maxcount()
    categories = sorted(Category.query.all(), key=lambda x: -x.posts.count())
    uncategorized_count = Post.query.filter(Post.categories==None).count()
    return render_template('archives.html', latest=latest, tags=tags,
        categories=categories, uncategorized_count=uncategorized_count, 
        months=months, max_count=max_count)
