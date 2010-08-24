# -*- coding: utf-8 -*-
"""
    Simblin Test Views
    ~~~~~~~~~~~~~~~~~~

    Test the different views of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import datetime
import flask

from simblin import create_app
from simblin.extensions import db
from simblin.models import Post, Tag, Category, post_tags, post_categories, Admin

from nose.tools import assert_equal
from test import TestCase

# TODO: Test archive view, Test month view 
# TODO: Test category view, test category deletion
# TODO: Make this leaner and put Model specific tests to test_models
#       Also look at danjac what he tests in test_views

class ViewTestCase(TestCase):
    """Base TestClass for views"""

    def register(self, username, password, password2='', email=''):
        """Helper function to register a user"""
        return self.client.post('/register', data=dict(
            username=username,
            password=password,
            password2=password2,
            email=email,
        ), follow_redirects=True)


    def login(self, username, password):
        """Helper function to login"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
        
        
    def register_and_login(self, username, password):
        """Register and login in one go"""
        self.register(username, password, password)
        self.login(username, password)


    def logout(self):
        """Helper function to logout"""
        return self.client.get('/logout', follow_redirects=True)


    def add_post(self, title, markup, tags=None, categories=[]):
        """Helper functions to create a blog post"""
        data=dict(
            title=title,
            markup=markup,
            tags=tags,
            action='Publish',
        )
        # Mimic select form fields
        for i, category_id in enumerate(categories):
            data['category-%d' % i] = category_id
        return self.client.post('/compose', data=data, follow_redirects=True)


    def update_post(self, slug, title, markup, tags=None, categories=[]):
        """Helper functions to create a blog post"""
        data=dict(
            title=title,
            markup=markup,
            tags=tags,
            action='Update',
        )
        # Mimic select form fields
        for i, category_id in enumerate(categories):
            data['category-%d' % i] = category_id
        return self.client.post('/update/%s' % slug, data=data, 
                                follow_redirects=True)
        

    def delete_post(self, slug):
        """Helper function to delete a blog post"""
        return self.client.post('/_delete/%s' % slug, data=dict(next=''), 
            follow_redirects=True)
            
            
    def add_category(self, name):
        """Register category in the database and return its id"""
        return flask.json.loads(
            self.client.post('/_add_category', data=dict(name=name)).data)['id']
    

class TestRegistration(ViewTestCase):
    
    def test_validation(self):
        """Test form validation"""
        self.clear_db()
        rv = self.register('', 'password')
        assert 'You have to enter a username' in rv.data
        rv = self.register('britney spears', '')
        assert 'You have to enter a password' in rv.data
        rv = self.register('barney', 'abv', 'abc')
        assert 'Passwords must match' in rv.data
    
    def test_registration(self):
        """Test successful registration and automatic login"""
        self.clear_db()
        with self.client:
            rv = self.register('barney', 'abc', 'abc')
            assert 'You are the new master of this blog' in rv.data
            assert flask.session['logged_in']
    
    def test_reregistration(self):
        """Test that only one admin can exist at a time and reregistration
        with new credentials only works when logged in"""
        self.clear_db()
        rv = self.register('barney', 'abc', 'abc')
        self.logout()            
        rv = self.register('barney', 'abc', 'abc')
        assert 'There can only be one admin' in rv.data
        self.login('barney', 'abc')
        rv = self.register('moe', 'ugly', 'ugly') # clears the admin
        rv = self.register('moe', 'ugly', 'ugly')
        assert 'You are the new master of this blog' in rv.data
        assert_equal(Admin.query.count(), 1)
        
        
class TestLogin(ViewTestCase):
    
    def test_validation(self):
        """Test form validation"""
        self.clear_db()
        self.register('barney', 'abc', 'abc')
        rv = self.login('borney', 'abc')
        assert 'Invalid username' in rv.data
        rv = self.login('barney', 'abd')
        assert 'Invalid password' in rv.data
        
    def test_login_logout(self):
        """Test logging in and out"""
        self.clear_db()
        self.register('barney', 'abc', 'abc')
        with self.client:   
            rv = self.login('barney', 'abc')
            assert 'You have been successfully logged in' in rv.data
            assert flask.session['logged_in']
            rv = self.logout()
            assert 'You have been successfully logged out' in rv.data
            assert 'logged_in' not in flask.session
        
        
class TestComposing(ViewTestCase):
    
    def test_validation(self):
        """Check if form validation and validation in general works"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        rv = self.add_post(title='', markup='a', tags='b')
        assert 'You must provide a title' in rv.data
        rv = self.update_post(title='a', markup='', tags='', slug='999x00')
        assert 'Invalid slug' in rv.data
        rv = self.add_post(title='a', markup='', tags='')
        assert 'New post was successfully posted' in rv.data
        
    def test_creation(self):
        """ Test the blog post's fields' correctness after adding/updating an 
        post and test the proper creation and automatic tidying of tags and
        tag mappings.
        """
        self.clear_db()
        self.register_and_login('barney', 'abc')
        
        title = "My post"
        markup = "# Title"
        tags = "django, franz und bertha,vil/bil"
        expected_id = 1
        expected_title = title
        expected_markup = markup
        expected_tags = ['django','franz-und-bertha','vil-bil']
        expected_slug = "my-post"
        first_slug = expected_slug
        expected_html = "<h1>Title</h1>"
        expected_date = datetime.date.today()
        self.add_post(title=title, markup=markup, tags=tags)
        post = Post.query.first()
        post_tagnames = [tag.name for tag in post.tags]
        
        assert_equal(post.id, expected_id)
        assert_equal(post.title, expected_title)
        assert_equal(post.markup, expected_markup)
        assert_equal(post.slug, expected_slug)
        assert expected_html in post.html
        assert_equal(post.datetime.date(), expected_date)
        assert_equal(sorted(post_tagnames), sorted(expected_tags))
        assert_equal([], post.categories)
        
        # Add another post with the same fields but expect a different slug
        # and the same number of tags inside the database
        
        expected_slug2 = expected_slug + '-2'
        tags2 = "django, franz und bertha"
        rv = self.add_post(title=title, markup=markup, tags=tags2)
        assert 'New post was successfully posted' in rv.data
        post = Post.query.filter_by(id=2).first()
        all_tags = Tag.query.all()
        
        assert_equal(post.title, expected_title) 
        assert_equal(post.slug, expected_slug2)
        assert_equal(len(all_tags), 3)    
        
        # Add yet another post with the same title and expect a different slug
        # Add some categories
        
        category1_id = self.add_category('cool')
        category2_id = self.add_category('cooler')
        expected_slug3 = expected_slug2 + '-2'
        self.add_post(title=title, markup=markup, tags=tags2, 
            categories=[category1_id, category1_id, category1_id, category2_id])
        post = Post.query.filter_by(id=3).first()
        category_names = [x.name for x in post.categories]
        
        assert_equal(post.slug, expected_slug3)
        assert_equal(Category.query.count(), 2)
        assert_equal(sorted(category_names), 
            sorted(['cool', 'cooler']))
        
        # Expect only two mappings although the mapping to the same category
        # has been added three times and to the other category once    
        post_category_mappings = db.session.query(post_categories).all()
        assert_equal(len(post_category_mappings), 2)
        
        # Now test updating an post
        
        updated_title = 'cool'
        updated_markup = '## Title'
        updated_tags = ''
        expected_title = updated_title
        expected_markup = updated_markup
        expected_tags = []
        expected_slug = 'cool'
        expected_html = '<h2>Title</h2>'
        expected_date = datetime.date.today()
        # Update the first post (slug=first_slug)
        self.update_post(title=updated_title, markup=updated_markup, 
            tags=updated_tags, slug=first_slug)
        post = Post.query.filter_by(id=1).first()
        post_tagnames = [tag.name for tag in post.tags]
        
        assert_equal(post.title, expected_title)
        assert_equal(post.markup, expected_markup)
        assert_equal(post.slug, expected_slug)
        assert expected_html in post.html
        assert_equal(post.datetime.date(), expected_date)
        assert_equal(sorted(post_tagnames), sorted(expected_tags))
        
        # update the same post without changing the title and expect the same
        # slug
        
        self.update_post(title=updated_title, markup=updated_markup, 
            tags=updated_tags, slug=expected_slug)
        post = Post.query.filter_by(id=1).first()
        assert_equal(post.slug, expected_slug)
        
        # Expect three rows in the posts table because three posts where
        # created and one updated. Expect only two rows in the tags table 
        # because the tag 'vil-bil' is not used anymore by an post. Also 
        # expect four posts in the post_tags table because it should look
        # like this:
        # post_id | tag_id
        # 2          1
        # 2          2
        # 3          1
        # 3          2
        
        posts = Post.query.all()
        tags = Tag.query.all()
        post_tag_mappings = db.session.query(post_tags).all()
        assert_equal(len(posts), 3)
        assert_equal(len(tags), 2)
        assert_equal(len(post_tag_mappings), 4)
        
        # TODO: Make class TestEntries and split actions to
        #       * validation * creation * updating * deletion * tags * categories


class TestDeletion(ViewTestCase):
    
    def test_deletion(self):
        """Test the deletion of a blog post and the accompanying deletion of
        tags"""
        self.register_and_login('barney', 'abc')
        
        self.add_post(title='Title', markup='', tags='cool')
        posts = Post.query.all()
        tags = Tag.query.all()
        
        assert_equal(len(posts), 1)
        assert_equal(len(tags), 1)
        
        rv = self.delete_post(slug='idontexist')
        assert 'No such post' in rv.data
        rv = self.delete_post(slug='title')
        assert 'Post deleted' in rv.data
        
        posts = Post.query.all()
        tags = Tag.query.all()
        
        assert_equal(len(posts), 0)
        assert_equal(len(tags), 0)


class TestPostView(ViewTestCase):
    
    def test_postview(self):
        """Test the displaying of one blog post"""
        self.register_and_login('barney', 'abc')
        
        self.add_post(title='Title', markup='', tags='')
        rv = self.client.get('/post/title')
        assert 'Title' in rv.data
