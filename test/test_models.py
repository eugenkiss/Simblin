# -*- coding: utf-8 -*-
"""
    Simblin Test Models
    ~~~~~~~~~~~~~~~~~~

    Test the different models of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
import datetime

from simblin import signals
from simblin.extensions import db
from simblin.models import Post, Tag, Category

from nose.tools import assert_equal, assert_true, assert_false
from test import TestCase


class TestPosts(TestCase):
    
    def test_post_creation(self):
        """Test if posts are created and saved properly to the database"""
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
        assert_true(post.comments_allowed)
        assert_true(post.visible)
        assert_equal(post.slug, expected_slug)
        assert expected_html in post.html
        assert_equal(post.datetime.date(), expected_date)
        assert_equal(sorted(tag.name for tag in post.tags), sorted(tags))
        assert_equal([], post.categories)
        
        # Add another post
        db.session.add(Post(title=title, markup=markup, comments_allowed=False,
            visible=False))
        db.session.commit()
        assert_false(Post.query.get(2).comments_allowed)
        assert_false(Post.query.get(2).visible)
        assert_equal(Post.query.count(), 2)
    
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
        
        
class TestTags(TestCase):
    
    def test_tag_creation(self):
        """Test if tags are created and saved properly to the database"""
        self.clear_db()
        db.session.add(Tag('cool'))
        db.session.commit()
        assert_equal(Tag.query.get(1).name, 'cool')
    
    def test_tag_associations(self):
        """Test if tags and posts are correctly associated with each other"""
        self.clear_db()
        db.session.add(Tag('cool'))
        db.session.add(Tag('cooler'))
        db.session.commit()
        post1 = Post(title='t', markup='')
        post1.tags = ['cool']
        post2 = Post(title='t2', markup='')
        post2.tags = ['cool', 'cooler']
        db.session.add(post1)
        db.session.add(post2)
        db.session.commit()
        
        assert_equal(Tag.query.get(1).posts.count(), 2) # cool
        assert_equal(Tag.query.get(2).posts.count(), 1) # cooler
        assert_equal(len(post1.tags), 1)
        assert_equal(post1.tags[0].name, 'cool')
        assert_equal(len(post2.tags), 2)
        assert_equal(post2.tags[0].name, 'cool')
        assert_equal(post2.tags[1].name, 'cooler')
    
    def test_tag_uniqueness(self):
        """Test if no duplicate tags are saved in the database"""
        self.clear_db()
        db.session.add(Tag.get_or_create('cool'))
        db.session.commit()
        tag = Tag.get_or_create('cool')
        db.session.add(tag)
        db.session.commit()
        
        assert_equal(Tag.query.count(), 1)
    
    def test_tag_tidying(self):
        """Test if tags are automatically deleted when a post is deleted
        and there are no tag associations after that"""
        self.clear_db()
        db.session.add(Tag('cool'))
        db.session.add(Tag('cooler'))
        db.session.commit()
        post1 = Post(title='t', markup='')
        post1.tags = ['cool']
        post2 = Post(title='t2', markup='')
        post2.tags = ['cool', 'cooler']
        db.session.add(post1)
        db.session.add(post2)
        db.session.commit()
        db.session.delete(post2)
        db.session.commit()
        signals.post_deleted.send(post2)
        
        assert_equal(Tag.query.count(), 1)
        assert_equal(Tag.query.first().name, 'cool')
    

class TestCategories(TestCase):
    
    def test_category_creation(self):
        """Test if categories are created and saved properly to the database"""
        self.clear_db()
        db.session.add(Category('cool'))
        db.session.commit()
        assert_equal(Category.query.get(1).name, 'cool')
    
    def test_tag_associations(self):
        """Test if categories and posts are correctly associated with 
        each other"""
        self.clear_db()
        db.session.add(Category('cool'))
        db.session.add(Category('cooler'))
        db.session.commit()
        post1 = Post(title='t', markup='')
        post1.categories = [1]
        post2 = Post(title='t2', markup='')
        post2.categories = [1, 2]
        db.session.add(post1)
        db.session.add(post2)
        db.session.commit()
        
        assert_equal(Category.query.get(1).posts.count(), 2) # cool
        assert_equal(Category.query.get(2).posts.count(), 1) # cooler
        assert_equal(len(post1.categories), 1)
        assert_equal(post1.categories[0].name, 'cool')
        assert_equal(len(post2.categories), 2)
        assert_equal(post2.categories[0].name, 'cool')
        assert_equal(post2.categories[1].name, 'cooler')
    
