Simblin
=======

*Sim*ple *Bl*og Eng*in*e - A blog engine written with [Flask][] and 
[SQLAlchemy][].

Simblin is built to be used by only one author. Simblin has no dashboard, no
plugin support and no theme support although the templates and css can be
modified by hand, of course. Simblin does not provide its own comment system
but has support for [Disqus][].

On the other hand Simblin delivers most features that are needed to provide a
good blogging experience. Simblin has 

* tags and categories
* post visibility (for drafts)
* markdown support
* archives
* source code highlighting
* feeds

See the changelog to see what featueres a specific version provides.

In order to run Simblin locally first create a database by running
`python initdb.py` and after that run `python run.py` and head over to
`http://localhost:5000/`. Drive your mouse to the top right corner to login.
You are going to be redirected to a registration page. Once registered you are
logged in with your credentials.


Deployment
----------

At first put your real settings in a file `settings.py` in the same folder where
the README is. You can look at `simblin/default-settings.cfg` to get an idea on
how to structure it.

Use a python shell to create a secret key:

    >>> import os
    >>> os.urandom(24)
    '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8' 

`setup.py` and `MANIFEST.in` are already configured for use with distribute.

Before you deploy Simblin you should create a virtual environment in your
server's project folder. Then you can use
[Fabric](http://flask.pocoo.org/docs/patterns/fabric/) to deploy Simblin. An
exemplary fabfile can look like this:

    from fabric.api import *

    # the user to use for the remote commands
    env.user = 'youruser'
    # the servers where the commands are executed
    env.hosts = ['yourhost']
    # the project dir (should be an absolute path)
    project_dir = '/var/www/simblin/'

    def pack():
        # create a new source distribution as tarball
        local('python setup.py sdist --formats=gztar', capture=False)

    def deploy():
        # figure out the release name and version
        dist = local('python setup.py --fullname').strip()
        # upload the source tarball to the temporary folder on the server
        put('dist/%s.tar.gz' % dist, '/tmp/simblin.tar.gz')
        
        # create a place where we can unzip the tarball, then enter
        # that directory and unzip it
        run('mkdir -p /tmp/simblin')
        with cd('/tmp/simblin'):
            run('tar xzf /tmp/simblin.tar.gz')
        # You have to be inside the folder where 'setup.py' resides
        with cd('/tmp/simblin/%s' % dist):
            # now setup the package with our virtual environment's
            # python interpreter
            run(project_dir+'env/bin/python setup.py install')
        # now that all is set up, delete the folder again
        run('rm -rf /tmp/simblin /tmp/simblin.tar.gz')
        
        ### Configuration files ###
        put('initdb.py', project_dir+'initdb.py')
        put('settings.py', project_dir+'settings.py')
        put('simblin.wsgi', project_dir+'simblin.wsgi')
        ### Database initialization ###
        # the environment variable needs to be set to create the database
        # at the specified uri in settings.py
        # note that the run command cannot be split into two commands because
        # the environment variable will not be preserved
        run('export SIMBLIN_SETTINGS='+project_dir+'settings.py;'+
            project_dir+'env/bin/python '+project_dir+'initdb.py')
        # so that the database is writable!!
        run('chmod -R g+w %s*' % project_dir)
        ### Static files ###
        # upload the static files separately so that you can use a web server
        # to serve static files
        run('mkdir -p '+project_dir+'static')
        put('simblin/static/*', project_dir+'static')
        
        ### Apache mod_wsgi ###
        # touch the .wsgi file so that mod_wsgi triggers a reload of the application
        run('touch '+project_dir+'simblin.wsgi')
        ### uwsgi ###
        # restart uwsgi processes by killing them thus reloading the application
        run('killall -9 uwsgi')
        
        
        def backup():
        """Back up the database"""
        import time
        get(project_dir+'simblin.db', 'backup/simblin-%d.db' % time.time())

Run `fab pack deploy` to deploy Simblin on your server. Run `fab backup` to
obtain a backup of the databse. Of course you can do it manually, too, so you
don't need to hassle with fabric.

Use `nosetests test` to run tests.

If you want to learn more about deployment and configuration of flask apps head
over to the [Flask Documentation](http://flask.pocoo.org/docs/).


### Cherokee 1.0.8 + uWSGI 0.9.6

This is a short instruction on how to configure the [cherokee][] webserver to
host Simblin simply because it's the setup I use. Besides cherokee you need of
course [uWSGI][].

  [uwsgi]: http://projects.unbit.it/uwsgi/
  [cherokee]: http://www.cherokee-project.com/

Inside cherokee-admin go to `Sources` and create a new one. For Example

    Nick: uWSGI 1
    Connection: 127.0.0.1:34340
    Interpreter: /usr/bin/uwsgi -s 127.0.0.1:34340 -t 10 -M -p 1 -C  --wsgi-file /your/path/simblin.wsgi
    
Create a new uWSGI Handler in your virtual server and add `uWSGI 1` as an
information source. Save and restart the server. Now everything should work. If
not try to restart the server from the command line 

    /etc/init.d/cherokee restart
    
In order to utilize caching add or configure the static content handler of your
virtual server by creating a directory match rule and entering `/static/` as the
web directory. On the time tab set the expiration to `Do not expire until 2038`.
This is ok because the static files are versionend by their last modification
date so that when a static file is modified the cache will be updated.


Q&A
---

### How do I login/create a post?

If you didn't change the default template you can drive your mouse to the top
right corner of the web page and a login link should appear. Once logged in you
can find a compose and a logout link there.


### How to create pages?

Pages are just blog posts. Just "hardcode" the link to a specific blog post in
your template. For example, if you want to have an `About` page put

    "{{ url_for('show_post', slug='about') }}"
    
in the `href` attribute of the link in your template to the `About` page.

This is not needed but I would recommend to put all blog posts which are
supposed to be pages in the category `Pages` and additionally I would disable
comments on them.


### How to use source code highlighting?

Source code highlighting is enabled by the [CodeColor][] extension of
[Markdown2][] and you don't have to be afraid to use underscores in your code
thanks to the [CodeFriendly][] extension.

  [codecolor]: http://code.google.com/p/python-markdown2/wiki/CodeColor
  [codefriendly]: http://code.google.com/p/python-markdown2/wiki/CodeFriendly


### What's the difference between categories and tags in Simblin?

Tags ought to describe the content of a blog post (what is it about?).
Categories on the other hand ought to state where a blog post belongs in.
Sometimes, however, the distinction between categories and tags is not clear.
 
Suppose you create a programming tutorial. One possibility is to not put it in a
category at all and instead tag it with `programming` and `tutorial`. Another
possiblity is to put it in the category `programming` and tag it with
`tutorial`. I, however, would put the post in the categories `programming` *and*
`tutorial` and add tags like `django` if, for instance, the tutorial is about
django.

Since a blog post, in my world view, can belong in different places it should be
able to be attached to several categories, too. Therefore categories are
essentially implemented like tags. However, tags are deleted automatically when
no posts reference a tag anymore. Categories are not.


### How to change username/password/email?

Once you registered you can go to `http://yourblog.com/register` to "reregister"
with new credentials. You must be logged in to do this. Beware: If you forget
to register with new credentials anybody who visits the blog can register as
the admin.


### How to supply images/files with a blog post?

There is no integrated way in Simblin. I would suggest that you upload your
files/images somewhere, for instance http://files.yourdomain.com/ or dropbox
etc., and link to them in your blog post.


### How to use comments?

Comments are provided by [Disqus][]. Head over to their website to learn more.
Basically you create an account and set the `DISQUS_SHORTNAME` option in your
`settings.py` accordingly. For further convenience you should specifiy the
`Cross-domain Receiver URL` on the Disqus settings page. Just put there
`http://yoursubdomain.yourdomain.com/does-not-exist`.


### How to create drafts?

When creating a post just uncheck `Visible?`. Doing so will hide the post from
all visitors but the admin. TODO: Be able to manually set the date.


### Why another blog engine?

1. Learn about web programming in general
2. Become more experienced with the excellent Flask framework 
3. Have a perfectly tailored blog for my website


### Do you really think anybody but you will use this shit?

No :), but I like to document my projects in a way as if they were meant for
others. This way I write more precise documentation which will be invaluable
for me after several weeks without working on the project.


Used libraries/frameworks
-------------------------

* [Flask][]
    * [Flask SQLAlchemy][]
    * [Flask Testing][]
    * [blinker][]
* [SQLAlchemy][]
* [Markdown2][]
    * [Pygments][]
* [rfc3339.py][]
* [JQuery][]
    * [Tab Override Plugin](http://plugins.jquery.com/project/tab-override)

  [markdown2]: http://code.google.com/p/python-markdown2/
  [flask]: http://flask.pocoo.org/
  [sqlalchemy]: http://www.sqlalchemy.org/
  [flask sqlalchemy]: http://packages.python.org/Flask-SQLAlchemy/
  [flask testing]: http://packages.python.org/Flask-Testing/
  [blinker]: http://discorporate.us/projects/Blinker/
  [pygments]: http://pygments.org/
  [disqus]: http://www.disqus.com/
  [jquery]: http://jquery.com/
  [rfc3339.py]: http://henry.precheur.org/projects/rfc3339
