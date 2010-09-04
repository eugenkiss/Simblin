# -*- coding: utf-8 -*-
"""
    Simblin Models
    ~~~~~~~~~~~~~~

    Database abstractions.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from werkzeug import check_password_hash, generate_password_hash
from flask import session
from flaskext.sqlalchemy import BaseQuery

from simblin.helpers import normalize, convert_markup
from simblin.extensions import db
from simblin import signals


class Admin(db.Model):
    """There should ever only be one admin"""
    
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True)
    pw_hash = db.Column(db.String(),)
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.pw_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)


class PostQuery(BaseQuery):
    
    def get_months(self):
        """Group by month and year and return month dict"""
        from itertools import groupby
        from calendar import month_name
        months = []
        ordered_posts = self.order_by(Post.id.desc())
        if not session.get('logged_in'): 
            ordered_posts = ordered_posts.filter_by(visible=True)
        def group_key(item): 
            return item.datetime.year, item.datetime.month
        for ((year, month), items) in groupby(ordered_posts, group_key):
            months.append(dict(
                year=year,
                index=month,
                name=month_name[month],
                count=len(list(items)),
            ))
        return months
    

class Post(db.Model):
    
    __tablename__ = 'posts'
    query_class = PostQuery
    
    id = db.Column(db.Integer, primary_key=True)
    _slug = db.Column(db.String(255), unique=True, nullable=False)
    _title = db.Column(db.String(255), nullable=False)
    _markup = db.Column(db.Text)
    _html = db.Column(db.Text)
    comments_allowed = db.Column(db.Boolean)
    visible = db.Column(db.Boolean)
    datetime = db.Column(db.DateTime)
    
    # Many to many Post <-> Tag
    _tags = db.relationship('Tag', secondary='post_tags', 
        backref=db.backref('posts', lazy='dynamic'))
    
    # Manty to many Post <-> Category
    _categories = db.relationship('Category', secondary='post_categories',
        backref=db.backref('posts', lazy='dynamic'))
    
    def __init__(self, title, markup='', comments_allowed=True, visible=True):
        self.title = title
        self.markup = markup
        self.datetime = datetime.now()
        self.comments_allowed = comments_allowed;
        self.visible = visible;
    
    def _set_title(self, title):
        """Constrain title with slug so slug is never set directly"""
        self._title = title
        slug = normalize(title)
        # Make the slug unique
        while True:
            entry = Post.query.filter_by(slug=slug).first()
            if not entry or entry == self: break
            slug += "-2"
        self._slug = slug
        
    def _get_title(self):
        return self._title
    
    title = db.synonym("_title", descriptor=property(_get_title, _set_title))
    
    def _get_slug(self):
        return self._slug
    
    slug = db.synonym("_slug", descriptor=property(_get_slug))
    
    def _set_markup(self, markup):
        """Constrain markup with html so html is never set directly"""
        self._markup = markup
        self._html = convert_markup(markup)
        
    def _get_markup(self):
        return self._markup
    
    markup = db.synonym('_markup', 
                        descriptor=property(_get_markup, _set_markup))
        
    def _get_html(self):
        return self._html
    
    html = db.synonym('_html', descriptor=property(_get_html))
    
    def _set_tags(self, taglist):
        """Associate tags with this entry. The taglist is expected to be already
        normalized without duplicates."""
        # Remove all previous tags
        self._tags = []
        for tag_name in taglist:
            self._tags.append(Tag.get_or_create(tag_name))
                
        
    def _get_tags(self):
        return self._tags
        
    tags = db.synonym("_tags", descriptor=property(_get_tags, _set_tags))
    
    def get_tagstring(self):
        """Return the tags of this post as a comma separated string"""
        return ', '.join([tag.name for tag in self._tags])
    
    def _set_categories(self, category_ids):
        """Associate categories with this entry by committing a list of
        category ids"""
        self._categories = []
        # Use set to prevent duplicate mappings
        for id in set(category_ids):
            self._categories.append(Category.query.get(id))
        
    def _get_categories(self):
        return self._categories
    
    categories = db.synonym("_categories", descriptor=property(_get_categories,
        _set_categories))
    
    def get_year(self):
        return self.datetime.year
    
    def get_month(self):
        return self.datetime.month
    
    def __repr__(self):
        return '<Post: %s>' % self.slug
    
    
# Association tables

post_tags = db.Table('post_tags', db.Model.metadata,
    db.Column('post_id', db.Integer, 
              db.ForeignKey('posts.id', ondelete='CASCADE')),
    db.Column('tag_id', db.Integer,
              db.ForeignKey('tags.id', ondelete='CASCADE')))

post_categories = db.Table('post_categories', db.Model.metadata,
    db.Column('post_id', db.Integer, 
              db.ForeignKey('posts.id', ondelete='CASCADE')),
    db.Column('category_id', db.Integer,
              db.ForeignKey('categories.id', ondelete='CASCADE')))


class TagQuery(BaseQuery):
    
    def get_maxcount(self):
        """Return the most used tag's number of associations. This is needed
        for the calculation of the tag cloud"""
        return max(tag.post_count for tag in self) if self.count() else 0


class Tag(db.Model):
    
    __tablename__ = 'tags'
    query_class = TagQuery
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    
    @classmethod
    def get_or_create(cls, tag_name):
        """Only add tags to the database that don't exist yet. If tag already
        exists return a reference to the tag otherwise a new instance"""
        tag = cls.query.filter(cls.name==tag_name).first()
        if not tag:
            tag = cls(tag_name)
        return tag
    
    def __init__(self, name):
        self.name = name
    
    @property
    def post_count(self):
        """Return the number of posts with this tag"""
        if not session.get('logged_in'):
            return self.posts.filter_by(visible=True).count()
        return self.posts.count()
    
    def __repr__(self):
        return '<Tag: %s>' % self.name
    

class Category(db.Model):
    
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    
    def __init__(self, name):
        self.name = name
    
    @property
    def post_count(self):
        """Return the number of posts in this category"""
        if not session.get('logged_in'):
            return self.posts.filter_by(visible=True).count()
        return self.posts.count()
    
    def __repr__(self):
        return '<Category: %s>' % self.name
    
    
# ------------- SIGNALS ----------------#

def tidy_tags(post):
    """Remove tags with zero associations"""
    for tag in Tag.query.filter_by(posts=None):
        db.session.delete(tag)
    db.session.commit()

signals.post_created.connect(tidy_tags)
signals.post_updated.connect(tidy_tags)
signals.post_deleted.connect(tidy_tags)
