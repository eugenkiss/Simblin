# -*- coding: utf-8 -*-
"""
    Simblin Main Views
    ~~~~~~~~~~~~~~~~~~

    The different views of the blogging application that are accessible by every
    visitor.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from flask import Module, current_app, render_template, flash, redirect, \
                  url_for, abort, session, make_response
from flaskext.sqlalchemy import Pagination

from simblin.extensions import db
from simblin.models import Post, Tag, Category


main = Module(__name__)


@main.route('/atom')
def atom_feed():
    """Create an atom feed from the posts"""
    from simblin.lib.rfc3339 import rfc3339
    posts = Post.query.filter_by(visible=True).order_by(Post.datetime.desc())
    updated = posts.first().datetime
    response = make_response(render_template('atom.xml', posts=posts, 
        updated=updated, rfc3339=rfc3339))
    response.mimetype = "application/atom+xml"
    return response

@main.route('/', defaults={'page':1})
@main.route('/<int:page>')
def show_posts(page):
    """Show the latest x blog posts"""
    if not session.get('logged_in'):
        posts = Post.query.filter_by(visible=True)
    else:
        posts = Post.query
    pagination = posts.order_by(Post.datetime.desc()).paginate(page=page, 
        per_page=current_app.config['POSTS_PER_PAGE'])
    if not pagination.total: flash("No posts so far")
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_posts', page=x))
        
        
@main.route('/post/<slug>')
def show_post(slug):
    """Show a specific blog post alone"""
    post = Post.query.filter_by(slug=slug).first()
    if not post: abort(404)
    if not session.get('logged_in') and not post.visible: abort(404)
    return render_template('post.html', post=post)
        

@main.route('/tag/<tag>/', defaults={'page':1})
@main.route('/tag/<tag>/<int:page>/')
def show_tag(tag, page):
    """Shows all posts with a specific tag"""
    per_page = current_app.config['POSTS_PER_PAGE']
    tag = Tag.query.filter_by(name=tag).first() or abort(404)
    posts = tag.posts.order_by(Post.id.desc())
    if not session.get('logged_in'): posts = posts.filter_by(visible=True)
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Posts tagged with '%s'" % tag.name)
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_tag', tag=tag.name, page=x))
        
        
@main.route('/category/<category>/', defaults={'page':1})
@main.route('/category/<category>/<int:page>/')
def show_category(category, page):
    """Shows all posts in a category"""
    per_page = current_app.config['POSTS_PER_PAGE']
    category = Category.query.filter_by(name=category).first() or abort(404)
    posts = category.posts.order_by(Post.id.desc())
    if not session.get('logged_in'): posts = posts.filter_by(visible=True)
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Posts in category '%s'" % category.name)
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_category', 
        category=category.name, page=x))
                                        
                                        
@main.route('/uncategorized/', defaults={'page':1})
@main.route('/uncategorized/<int:page>/')
def show_uncategorized(page):
    """Shows all posts which aren't in any category"""
    per_page = current_app.config['POSTS_PER_PAGE']
    posts = Post.query.filter(Post.categories==None)
    if not session.get('logged_in'): posts = posts.filter_by(visible=True)
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    flash("Uncategorized posts")
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_uncategorized', page=x))
        
        
@main.route('/<int:year>/<int:month>/', defaults={'page':1})
@main.route('/<int:year>/<int:month>/<int:page>/')
def show_month(year, month, page):
    """Show all posts from a specific year and month"""
    from calendar import month_name
    if month not in range(1, 13): abort(404)
    per_page = current_app.config['POSTS_PER_PAGE']
    posts = Post.query.filter(db.extract('year', Post.datetime)==year)
    posts = posts.filter(db.extract('month', Post.datetime)==month)
    posts = posts.order_by(Post.id.desc()) 
    if not session.get('logged_in'): posts = posts.filter_by(visible=True)
    items = posts.limit(per_page).offset((page - 1) * per_page).all()
    pagination = Pagination(posts, page=page, per_page=per_page, 
        total=posts.count(), items=items)
    if items:
        flash("Posts from %s %d" % (month_name[month], year))
    else:
        flash("No entries here so far")
    return render_template('posts.html', pagination=pagination,
        endpoint_func=lambda x: url_for('main.show_month', year=year, month=month, 
        page=x))
        
        
@main.route('/archives/')
def show_archives():
    """Show the archive. That is recent posts, posts by category etc."""
    if not session.get('logged_in'): 
        latest = Post.query.filter_by(visible=True)
    else:
        latest = Post.query
    latest = latest.order_by(Post.id.desc()).limit(10)
    months = Post.query.get_months()
    tags = Tag.query.order_by(Tag.name).all()
    #: Needed for calculation of tag cloud
    max_count = Tag.query.get_maxcount()
    categories = sorted(Category.query.all(), key=lambda x: -x.post_count)
    uncategorized_count = Post.query.filter(Post.categories==None).count()
    return render_template('archives.html', latest=latest, tags=tags,
        categories=categories, uncategorized_count=uncategorized_count, 
        months=months, max_count=max_count)
