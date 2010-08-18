# -*- coding: utf-8 -*-
"""
    Simblin Test Models
    ~~~~~~~~~~~~~~~~~~

    Test the different models of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from simblin.extensions import db
from simblin.models import Post, Tag, Category, post_tags, post_categories

from nose.tools import assert_equal
from test import TestCase


class TestPosts(TestCase):
    
    def test_post_creation(self):
        self.clear_db()
        title = "My post"
        markup = "# Title"
        tags = ['django','franz-und-bertha','vil-bil']
        expected_slug = "my-post"
        expected_html = "<h1>Title</h1>"
        expected_date = datetime.date.today()
        
        post = Post(title=title, markup=markup)
        post.tags = tags
        db.session.add(post)
        db.session.commit()
        
        assert_equal(post.title, title)
        assert_equal(post.markup, markup)
        assert_equal(post.slug, expected_slug)
        assert expected_html in post.html
        assert_equal(post.datetime.date(), expected_date)
        assert_equal(sorted(tag.name for tag in post.tags), sorted(tags))
        assert_equal([], post.categories)
        
        # Add another post
        db.session.add(Post(title=title, markup=markup))
        db.session.commit()
        assert_equal(len(Post.query.all()), 2)
    
    def test_slug_uniqueness(self):
        """Test if posts with the same title result in different slugs"""
        self.clear_db()
        for i in range(3):
            post = Post(title='t', markup='')
            db.session.add(post)
            db.session.commit()
        
        posts = Post.query.all()
        assert_equal(posts[0].slug, 't')
        assert_equal(posts[1].slug, 't-2')
        assert_equal(posts[2].slug, 't-2-2')
        
    def test_same_slug_after_updating(self):
        """Test if updating a post without changing the title does not result
        in a different slug (regression)"""
        self.clear_db()
        post = Post(title='t', markup='')
        db.session.add(post)
        db.session.commit()
        post.title = 't'
        db.session.commit()
        assert_equal(post.slug, 't')
    
    def test_months_view(self):
        """Test the month objects for the archive view"""
        self.clear_db()
        datetimes = [
            datetime.datetime(2000, 1, 1),
            datetime.datetime(2000, 1, 2),
            datetime.datetime(2000, 2, 3),
            datetime.datetime(2002, 2, 4),
        ]
        for date in datetimes:
            post = Post(title='t', markup='')
            post.datetime = date
            db.session.add(post)
            db.session.commit()

        months = Post.query.get_months()
        assert_equal(len(months), 3)
        assert_equal(months[0]['year'], 2002)
        assert_equal(months[0]['index'], 2)
        assert_equal(months[0]['count'], 1)
        assert_equal(months[2]['year'], 2000)
        assert_equal(months[2]['index'], 1)
        assert_equal(months[2]['count'], 2)
