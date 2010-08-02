from __future__ import with_statement
import datetime
import tempfile
import os

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
#: The connection to the temporary database
db = None
#: The context of the application
ctx = None
    
    
def setUp():
    """Initalize application and temporary database"""
    global db_tempfile, app, client, db, ctx
    db_tempfile, config.DATABASE = tempfile.mkstemp()
    app = create_app(config)
    client = app.test_client()
    helpers.init_db(config.DATABASE, app=app)
    db = helpers.connect_db(config.DATABASE)
    ctx = app.test_request_context()
    ctx.push()


def teardown():
    """Get rid of the database again"""
    os.close(db_tempfile)
    os.unlink(config.DATABASE)
    ctx.pop()
    
    
def clear_db():
    """Remove all rows inside the database"""
    helpers.init_db(config.DATABASE, app=app)
    
    
# Helper functions

def query_db(query, args=(), one=False):
    return helpers.query_db(query, args, one, db=db)


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
    """Registers and logs in in one go"""
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


def update_entry(title, markdown, tags, id):
    """Helper functions to create a blog post"""
    return client.post('/compose', data=dict(
        title=title,
        markdown=markdown,
        tags=tags,
        id=id
    ), follow_redirects=True)
        
        
class TestRegister:
    
    def test_redirect(self):
        """
        If there is no admin yet the visitor shall be redirected 
        to the register page.
        """
        clear_db()
        rv = client.get('/', follow_redirects=True)
        print rv.data
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
        rv = register('barney', 'abc', 'abc')
        assert 'You are the new master of this blog' in rv.data
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
        rv = login('barney', 'abc')
        assert 'You have been successfully logged in' in rv.data
        # TODO: Test if session.logged_in has been set
        rv = logout()
        assert 'You have been successfully logged out' in rv.data
        
        
class TestComposing:
    
    def test_validation(self):
        """Check if form validation and validation in general works"""
        clear_db()
        register_and_login('barney', 'abc')
        rv = add_entry(title='', markdown='a', tags='b')
        assert 'You must provide a title' in rv.data
        rv = add_entry(title='a', markdown='', tags='')
        assert 'New entry was successfully posted' in rv.data
        rv = update_entry(title='a', markdown='', tags='', id=999)
        assert 'Invalid id' in rv.data
        rv = client.get('/compose?id=999')
        assert 'Invalid id' in rv.data
        
    def test_conversion(self):
        """
        Test the blog post's fields' correctness after adding/updating an entry
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
        expected_html = "<h1>Title</h1>"
        expected_date = datetime.date.today()
        add_entry(title=title, markdown=markdown, tags=tags)
        entry = query_db('SELECT * FROM entries', one=True)
        tags = helpers.get_tags(entry['id'], db=db)
        
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
        update_entry(title=updated_title, markdown=updated_markdown, 
            tags=updated_tags, id=1)
        entry = query_db('SELECT * FROM entries WHERE id=1', one=True)
        tags = helpers.get_tags(entry_id=entry['id'], db=db)
        
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


class TestEntryView:
    
    def test_entryview(self):
        clear_db()
        register_and_login('barney', 'abc')
        
        add_entry(title='Title', markdown='', tags='')
        rv = client.get('/entry/title')
        assert 'Title' in rv.data
