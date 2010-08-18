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

from nose.tools import assert_equal

from simblin import create_app
from simblin.extensions import db
from simblin.models import Post, Tag, Category, post_tags, post_categories

# TODO: Test archive view, Test month view

# Configuration

#: Inmemory database
SQLALCHEMY_DATABASE_URI = 'sqlite://'

# Globals
#: The application
app = None
#: The test client   
client = None
#: The context of the application
ctx = None
    
    
def setUp():
    """Initalize application and temporary database"""
    global app, client, ctx
    app = create_app(__name__)
    client = app.test_client()
    ctx = app.test_request_context()
    ctx.push()
    db.init_app(app)
    db.create_all()


def teardown():
    """Get rid of the context"""
    ctx.pop()
    
    
def clear_db():
    """Remove all rows inside the database"""
    ctx.push() # If I remove this test_registering won't work?
    db.session.remove()
    db.drop_all()
    db.create_all()
    
    
# Helper functions

class faked_request:
    """Use with the `with` statement. Simulates the `before_request` and 
    `after_request` actions."""
    
    def __enter__(self):
        """Initialize db connections, g, request etc."""
        ctx.push()
        app.preprocess_request()
        
    def __exit__(self, type, value, traceback):
        """Close db connections, g, request etc."""
        app.process_response(app.response_class())
        ctx.pop()


def register(username, password, password2='', email=''):
    """Helper function to register a user"""
    return client.post('/register', data=dict(
        username=username,
        password=password,
        password2=password2,
        email=email,
    ), follow_redirects=True)


def login(username, password):
    """Helper function to login"""
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)
    
    
def register_and_login(username, password):
    """Register and login in one go"""
    register(username, password, password)
    login(username, password)


def logout():
    """Helper function to logout"""
    return client.get('/logout', follow_redirects=True)


def add_post(title, markup, tags=None, categories=[]):
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
    return client.post('/compose', data=data, follow_redirects=True)


def update_post(slug, title, markup, tags=None, categories=[]):
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
    return client.post('/update/%s' % slug, data=data, follow_redirects=True)
    

def delete_post(slug):
    """Helper function to delete a blog post"""
    return client.post('/_delete/%s' % slug, data=dict(next=''), 
        follow_redirects=True)
        
        
def add_category(name):
    """Register category in the database and return its id"""
    return flask.json.loads(
        client.post('/_add_category', data=dict(name=name)).data)['id']
    

# Tests
        
class TestRegistration:
    
    def test_registering(self):
        """Test form validation and successful registering"""
        clear_db()
        rv = register('', 'password')
        assert 'You have to enter a username' in rv.data
        rv = register('britney spears', '')
        assert 'You have to enter a password' in rv.data
        rv = register('barney', 'abv', 'abc')
        assert 'Passwords must match' in rv.data
        with client:
            rv = register('barney', 'abc', 'abc')
            assert 'You are the new master of this blog' in rv.data
            assert flask.session['logged_in']
        logout()            
        rv = register('barney', 'abc', 'abc')
        assert 'There can only be one admin' in rv.data
        

class TestLogin:
    
    def test_login(self):
        clear_db()
        register('barney', 'abc', 'abc')
        rv = login('borney', 'abc')
        assert 'Invalid username' in rv.data
        rv = login('barney', 'abd')
        assert 'Invalid password' in rv.data
        # In order to keep the context around
        with client:   
            rv = login('barney', 'abc')
            assert 'You have been successfully logged in' in rv.data
            assert flask.session['logged_in']
            rv = logout()
            assert 'You have been successfully logged out' in rv.data
            assert 'logged_in' not in flask.session
        
        
class TestComposing:
    
    def test_validation(self):
        """Check if form validation and validation in general works"""
        clear_db()
        register_and_login('barney', 'abc')
        rv = add_post(title='', markup='a', tags='b')
        assert 'You must provide a title' in rv.data
        rv = add_post(title='a', markup='', tags='')
        assert 'New post was successfully posted' in rv.data
        rv = update_post(title='a', markup='', tags='', slug='999x00')
        assert 'Invalid slug' in rv.data
        
    def test_creation(self):
        """ Test the blog post's fields' correctness after adding/updating an 
        post and test the proper creation and automatic tidying of tags and
        tag mappings.
        """
        clear_db()
        register_and_login('barney', 'abc')
        
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
        add_post(title=title, markup=markup, tags=tags)
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
        add_post(title=title, markup=markup, tags=tags2)
        post = Post.query.filter_by(id=2).first()
        all_tags = Tag.query.all()
        
        assert_equal(post.title, expected_title) 
        assert_equal(post.slug, expected_slug2)
        assert_equal(len(all_tags), 3)    
        
        # Add yet another post with the same title and expect a different slug
        # Add some categories
        
        category1_id = add_category('cool')
        category2_id = add_category('cooler')
        expected_slug3 = expected_slug2 + '-2'
        add_post(title=title, markup=markup, tags=tags2, 
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
        update_post(title=updated_title, markup=updated_markup, 
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
        
        update_post(title=updated_title, markup=updated_markup, 
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
        
        # TODO: Test Get all posts by a tag
        # TODO: Make class TestEntries and split actions to
        #       * validation * creation * updating * deletion * tags * categories


class TestDeletion:
    
    def test_deletion(self):
        """Test the deletion of a blog post and the accompanying deletion of
        tags"""
        clear_db()
        register_and_login('barney', 'abc')
        
        add_post(title='Title', markup='', tags='cool')
        posts = Post.query.all()
        tags = Tag.query.all()
        
        assert_equal(len(posts), 1)
        assert_equal(len(tags), 1)
        
        rv = delete_post(slug='idontexist')
        print rv.data
        assert 'No such post' in rv.data
        rv = delete_post(slug='title')
        assert 'Post deleted' in rv.data
        
        posts = Post.query.all()
        tags = Tag.query.all()
        
        assert_equal(len(posts), 0)
        assert_equal(len(tags), 0)


class TestPostView:
    
    def test_postview(self):
        """Test the displaying of one blog post"""
        clear_db()
        register_and_login('barney', 'abc')
        
        add_post(title='Title', markup='', tags='')
        rv = client.get('/post/title')
        assert 'Title' in rv.data
