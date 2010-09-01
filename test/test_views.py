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

from simblin.extensions import db
from simblin.models import Post, Tag, Category, post_tags, post_categories, Admin

from nose.tools import assert_equal, assert_true, assert_false
from test import TestCase


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

    def add_post(self, title, markup='', comments_allowed=None, visible=None,
        tags='', categories=[]):
        """Helper functions to create a blog post"""
        data=dict(
            title=title,
            markup=markup,
            tags=tags,
            action='Publish',
        )
        if comments_allowed is not None: 
            data['comments_allowed'] = True
        if visible is not None: 
            data['visible'] = True
        # Mimic select form fields
        for i, category_id in enumerate(categories):
            data['category-%d' % i] = category_id
        return self.client.post('/compose', data=data, follow_redirects=True)

    def update_post(self, slug, title, markup='', comments_allowed=None, 
        visible=None, tags=None, categories=[]):
        """Helper functions to create a blog post"""
        data=dict(
            title=title,
            markup=markup,
            tags=tags,
            action='Update',
        )
        if comments_allowed is not None: 
            data['comments_allowed'] = True
        if visible is not None: 
            data['visible'] = True
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
            
    def delete_category(self, id):
        return self.client.post('/_delete_category', data=dict(id=id))
            
    
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
        
        
class TestPost(ViewTestCase):
    """Tags and categories are tested alongside"""
    
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
        """Test the blog post's fields' correctness after adding an 
        post and test proper category association"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        
        title = "My post"
        markup = "# Title"
        tags = "django, franz und bertha,vil/bil"
        category1_id = self.add_category('cool')
        category2_id = self.add_category('cooler')
        self.add_post(title=title, markup=markup, tags=tags,
            categories=[category1_id, category1_id, category2_id])
            
        post = Post.query.get(1)
        post_tagnames = [tag.name for tag in post.tags]
        category_names = [x.name for x in post.categories]
        
        assert_equal(post.id, 1)
        assert_equal(post.title, title)
        assert_equal(post.markup, markup)
        assert_false(post.comments_allowed)
        assert_false(post.visible)
        assert_equal(post.slug, 'my-post')
        assert '<h1>Title</h1>' in post.html
        assert_equal(post.datetime.date(), datetime.date.today())
        assert_equal(sorted(post_tagnames), 
            sorted(['django','franz-und-bertha','vil-bil']))
        assert_equal(sorted(category_names), sorted(['cool', 'cooler']))
        
        assert_equal(Tag.query.count(), 3)
        assert_equal(Category.query.count(), 2)
        assert_equal(db.session.query(post_tags).count(), 3)
        # Expect only two mappings although the mapping to category1
        # has been added twice  
        assert_equal(db.session.query(post_categories).count(), 2)
        
        # Add another post
        self.add_post(title=post.title, tags=['django'], comments_allowed=True,
            visible=True)
        post2 = Post.query.get(2)
        
        assert_equal(post2.title, post.title) 
        assert_true(post2.comments_allowed)
        assert_true(post2.visible)
        assert_equal(post2.slug, post.slug + '-2')
        assert_equal(post2.categories, [])
        assert_equal(Tag.query.count(), 3)
        
        return post
    
    def test_updating(self):
        """Test the blog post's fields' correctness after updating a post and
        test the proper creation and automatic tidying of tags and tag
        mappings and category associations"""
        post = self.test_creation()
        datetime = post.datetime
        
        self.update_post(title='cool', markup='## Title', slug=post.slug, 
            tags=['django'], comments_allowed=True, visible=True)
        updated_post = Post.query.get(1)
        
        assert_equal(updated_post.title, 'cool')
        assert_equal(updated_post.markup, '## Title')
        assert_true(updated_post.comments_allowed)
        assert_true(updated_post.visible)
        assert_equal(updated_post.slug, 'cool')
        assert '<h2>Title</h2>' in updated_post.html
        assert_equal(updated_post.datetime, datetime)
        assert_equal([x.name for x in updated_post.tags], ['django'])
        
        # Expect two rows in the posts table because two posts were
        # created and one updated. Expect only one row in the tags table 
        # because only 'django' is used as a tag.
        
        assert_equal(Post.query.count(), 2)
        assert_equal(Tag.query.count(), 1)
        
        # Because there are two post with a tag expect two rows
        # in the post_tag association table
        
        assert_equal(db.session.query(post_tags).count(), 2)
        
        # Because there is no post in a category anymore expect not rows
        # in the post_categories association table
        
        assert_equal(db.session.query(post_categories).count(), 0)
    
    def test_deletion(self):
        """Test the deletion of a blog post and the accompanying deletion of
        tags"""
        self.clear_db()
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
    
    def test_singleview(self):
        """Test the displaying of one blog post"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        
        self.add_post(title='Title', markup='', visible=True)
        rv = self.client.get('/post/title')
        self.assert_200(rv)
        assert 'Title' in rv.data
        
        self.add_post(title='Title2', visible=None)
        rv = self.client.get('/post/title2')
        self.assert_200(rv)
        assert 'Title2' in rv.data
        
        self.logout()
        
        rv = self.client.get('/post/title')
        self.assert_200(rv)
        assert 'Title' in rv.data
        
        rv = self.client.get('/post/title2')
        self.assert_404(rv)
    
    def test_multipleview(self):
        """Test the displaying of multiple blog posts on home page"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        
        self.add_post(title='Title', markup='', visible=True)
        self.add_post(title='Title2', visible=None)
        
        self.logout()
        
        rv = self.client.get('/')
        self.assert_200(rv)
        assert 'Title' in rv.data
        assert 'Title2' not in rv.data
    

class TestArchives(ViewTestCase):
    
    def test_archives_page(self):
        """Test the displaying of the archives page"""
        self.clear_db()
        rv = self.client.get('/archives/')
        self.assert_200(rv)
        
    def test_month_view(self):
        """Test the displaying of the month view"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        post = Post('the chronic 2001', visible=False)
        post.datetime = datetime.datetime(1999, 11, 16)
        db.session.add(post)
        db.session.commit()
        rv = self.client.get('/1999/11/')
        self.assert_200(rv)
        assert 'the chronic 2001' in rv.data
        rv = self.client.get('/7777/12/')
        assert 'No entries here so far' in rv.data
        rv = self.client.get('/1999/14/')
        self.assert_404(rv)
        
        self.logout()
        rv = self.client.get('/1999/11/')
        self.assert_200(rv)
        assert 'No entries here so far' in rv.data


class TestTag(ViewTestCase):
    
    def test_view(self):
        """Test the displaying of the tag view"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        tag = Tag('drdre')
        db.session.add(tag)
        db.session.commit()
        post = Post('the chronic 2001', visible=True)
        post2 = Post('the chronic 2002', visible=False)
        post._tags = [tag]
        post2._tags = [tag]
        db.session.add(post)
        db.session.add(post2)
        db.session.commit()
        rv = self.client.get('/tag/drdre/')
        self.assert_200(rv)
        assert 'the chronic 2001' in rv.data
        rv = self.client.get('/tag/bobbybrown/')
        self.assert_404(rv)
        
        self.logout()
        rv = self.client.get('/tag/drdre/')
        self.assert_200(rv)
        assert 'the chronic 2001' in rv.data
        assert 'the chronic 2002' not in rv.data
        
        
class TestCategory(ViewTestCase):
    
    def test_view(self):
        """Test the displaying of the category view"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        category = Category('drdre')
        db.session.add(category)
        db.session.commit()
        post = Post('the chronic', visible=True)
        post2 = Post('the chrinoc', visible=False)
        post._categories = [category]
        post2._categories = [category]
        db.session.add(post)
        db.session.add(post2)
        db.session.commit()
        rv = self.client.get('/category/drdre/')
        self.assert_200(rv)
        assert 'the chronic' in rv.data
        rv = self.client.get('/category/sugeknight/')
        self.assert_404(rv)
        
        self.logout()
        rv = self.client.get('/category/drdre/')
        self.assert_200(rv)
        assert 'the chronic' in rv.data
        assert 'the chrinoc' not in rv.data
        
        rv = self.client.get('/uncategorized/')
        self.assert_200(rv)
        assert 'Uncategorized posts' in rv.data
        post2 = Post('dancing in the moonlight')
        db.session.add(post2)
        db.session.commit()
        rv = self.client.get('/uncategorized/')
        self.assert_200(rv)
        assert 'dancing in the moonlight' in rv.data
    
    def test_deletion_view(self):
        """Test if deletion works properly"""
        self.clear_db()
        self.register_and_login('barney', 'abc')
        category = Category('drdre')
        db.session.add(category)
        db.session.commit()
        assert_equal(Category.query.count(), 1)
        rv = self.delete_category(1)
        print rv
        assert_equal(Category.query.count(), 0)
