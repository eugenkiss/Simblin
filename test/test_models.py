# -*- coding: utf-8 -*-
"""
    Simblin Test Models
    ~~~~~~~~~~~~~~~~~~

    Test the different models of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import datetime
import flask

from simblin import create_app
from simblin.extensions import db
from simblin.models import Post, Tag, Category, post_tags, post_categories

from nose.tools import assert_equal
from test import TestCase


class TestPosts(TestCase):
    
    def test_months_view(self):
        """Test the month objects for the archive view"""
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
