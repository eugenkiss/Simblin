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
import tempfile
import os
import flask

from flask import g
from nose.tools import assert_equal, assert_true, assert_false, with_setup
from simblin import create_app, helpers


# Configuration
class config:
    DATABASE = None

#: File Pointer to temporary database
db_tempfile = None
#: The application
app = None
#: The test client   
client = None
#: The context of the application
ctx = None
    
    
def setUp():
    """Initalize application and temporary database"""
    global db_tempfile, app, client, ctx
    db_tempfile, config.DATABASE = tempfile.mkstemp()
    app = create_app(config)
    client = app.test_client()
    ctx = app.test_request_context()
    #: Because init_db uses current_app there must already be a context?
    ctx.push()
    helpers.init_db(app.config['DATABASE'])


def teardown():
    """Get rid of the database again"""
    os.close(db_tempfile)
    os.unlink(app.config['DATABASE'])
    ctx.pop()
    
    
def clear_db():
    """Remove all rows inside the database"""
    #: Because init_db uses current_app there must already be a context?
    ctx.push()
    helpers.init_db(app.config['DATABASE'])
    
    
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


def query_db(query, args=(), one=False):
    # `query_db` needs an openend database connection so the request must be
    # faked.
    with faked_request():
        return helpers.query_db(query, args, one)


def register(username, password, password2=None):
    """Helper function to register a user"""
    return client.post('/register', data=dict(
        username=username,
        password=password,
        password2=password2
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


def add_entry(title, markdown, tags):
    """Helper functions to create a blog post"""
    return client.post('/compose', data=dict(
        title=title,
        markdown=markdown,
        tags=tags,
        id=''
    ), follow_redirects=True)


def update_entry(title, markdown, tags, slug):
    """Helper functions to create a blog post"""
    return client.post('/update/%s' % slug, data=dict(
        title=title,
        markdown=markdown,
        tags=tags,
    ), follow_redirects=True)
    

def delete_entry(slug):
    """Helper function to delete a blog post"""
    return client.post('/delete/%s' % slug, data=dict(next=''), 
        follow_redirects=True)
        
        
class TestRegistration:
    
    def test_redirect(self):
        """
        If there is no admin yet the visitor shall be redirected 
        to the register page.
        """
        clear_db()
        logout()
        rv = client.get('/', follow_redirects=True)
        assert 'Register' in rv.data
    
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
        rv = add_entry(title='', markdown='a', tags='b')
        assert 'You must provide a title' in rv.data
        rv = add_entry(title='a', markdown='', tags='')
        assert 'New entry was successfully posted' in rv.data
        rv = update_entry(title='a', markdown='', tags='', slug='999x00')
        assert 'Invalid slug' in rv.data
        
    def test_conversion(self):
        """ Test the blog post's fields' correctness after adding/updating an 
        entry and test the proper creation and automatic tidying of tags and
        tag mappings.
        """
        clear_db()
        register_and_login('barney', 'abc')
        
        title = "My entry"
        markdown = "# Title"
        tags = "django, franz und bertha,vil/bil"
        expected_id = 1
        expected_title = title
        expected_markdown = markdown
        expected_tags = ['django','franz-und-bertha','vil-bil']
        expected_slug = "my-entry"
        first_slug = expected_slug
        expected_html = "<h1>Title</h1>"
        expected_date = datetime.date.today()
        add_entry(title=title, markdown=markdown, tags=tags)
        entry = query_db('SELECT * FROM entries', one=True)
        # In order to open a database connection to retrieve the tags
        with faked_request():
            tags = helpers.get_tags(entry['id'])
        
        assert_equal(entry['id'], expected_id)
        assert_equal(entry['title'], expected_title)
        assert_equal(entry['markdown'], expected_markdown)
        assert_equal(entry['slug'], expected_slug)
        assert expected_html in entry['html']
        assert_equal(entry['published'].date(), expected_date)
        assert_equal(tags, expected_tags)
        
        # Add another entry with the same fields but expect a different slug
        # and the same number of tags inside the database
        
        expected_slug2 = expected_slug + '-2'
        tags2 = "django, franz und bertha"
        add_entry(title=title, markdown=markdown, tags=tags2)
        entry = query_db('SELECT * FROM entries WHERE id=2', one=True)
        all_tags = query_db('SELECT * FROM tags')
        
        assert_equal(entry['title'], expected_title) 
        assert_equal(entry['slug'], expected_slug2)
        assert_equal(len(all_tags), 3)    
        
        # Add yet another entry with the same title and expect a different slug
        
        expected_slug3 = expected_slug2 + '-2'
        add_entry(title=title, markdown=markdown, tags=tags2)
        entry = query_db('SELECT * FROM entries WHERE id=3', one=True)
        
        assert_equal(entry['slug'], expected_slug3)
        
        # Now test updating an entry
        
        updated_title = 'cool'
        updated_markdown = '## Title'
        updated_tags = ''
        expected_title = updated_title
        expected_markdown = updated_markdown
        expected_tags = []
        expected_slug = 'cool'
        expected_html = '<h2>Title</h2>'
        expected_date = datetime.date.today()
        # Update the first entry (slug=first_slug)
        update_entry(title=updated_title, markdown=updated_markdown, 
            tags=updated_tags, slug=first_slug)
        entry = query_db('SELECT * FROM entries WHERE id=1', one=True)
        with faked_request():
            tags = helpers.get_tags(entry_id=entry['id'])
        
        assert_equal(entry['title'], expected_title)
        assert_equal(entry['markdown'], expected_markdown)
        assert_equal(entry['slug'], expected_slug)
        assert expected_html in entry['html']
        assert_equal(entry['published'].date(), expected_date)
        assert_equal(tags, expected_tags)
        
        # Expect three rows in the entries table because three entries where
        # created and one updated. Expect only two rows in the tags table 
        # because the tag 'vil/bil' is not used anymore by an entry. Also 
        # expect four entries in the entry_tag table because it should look
        # like this:
        # entry_id | tag_id
        # 2          1
        # 2          2
        # 3          1
        # 3          2
        
        entries = query_db('SELECT * FROM entries')
        tags = query_db('SELECT * FROM tags')
        entry_tag_mappings = query_db('SELECT * FROM entry_tag')
        assert_equal(len(entries), 3)
        assert_equal(len(tags), 2)
        assert_equal(len(entry_tag_mappings), 4)


class TestDeletion:
    
    def test_deletion(self):
        """Test the deletion of a blog post and the accompanying deletion of
        tags and their mappings to a blog post"""
        clear_db()
        register_and_login('barney', 'abc')
        
        add_entry(title='Title', markdown='', tags='cool')
        entries = query_db('SELECT * FROM entries')
        tags = query_db('SELECT * FROM tags')
        entry_tag_mappings = query_db('SELECT * FROM entry_tag')
        
        assert_equal(len(entries), 1)
        assert_equal(len(tags), 1)
        assert_equal(len(entry_tag_mappings), 1)
        
        rv = delete_entry(slug='idontexist')
        assert 'No such entry' in rv.data
        rv = delete_entry(slug='title')
        assert 'Entry deleted' in rv.data
        
        entries = query_db('SELECT * FROM entries')
        tags = query_db('SELECT * FROM tags')
        entry_tag_mappings = query_db('SELECT * FROM entry_tag')
        
        assert_equal(len(entries), 0)
        assert_equal(len(tags), 0)
        assert_equal(len(entry_tag_mappings), 0)


class TestEntryView:
    
    def test_entryview(self):
        """Test the displaying of one blog post"""
        clear_db()
        register_and_login('barney', 'abc')
        
        add_entry(title='Title', markdown='', tags='')
        rv = client.get('/entry/title')
        assert 'Title' in rv.data
