# -*- coding: utf-8 -*-
"""
    Simblin Test Helpers
    ~~~~~~~~~~~~~~~~~~~~

    Test the different utility functions of the blogging application.

    :copyright: (c) 2010 by Eugen Kiss.
    :license: BSD, see LICENSE for more details.
"""
from nose.tools import assert_equal

from simblin import helpers
    
            
def test_slug_normalizing():
    assert_equal(helpers.normalize(''), '')
    assert_equal(helpers.normalize('dadada'), 'dadada')
    assert_equal(helpers.normalize('DaDaDa'), 'dadada')
    assert_equal(helpers.normalize('The house'), 'the-house')
    assert_equal(helpers.normalize('The  house'), 'the-house')
    assert_equal(helpers.normalize(' 123-name '), '123-name')
    assert_equal(helpers.normalize('a?b&c>d<e=f/g'), 'a-b-c-d-e-f-g')
    
    
def test_tags_normalizing():
    """Test the correct interpretation of a string of comma separated tags"""
    assert_equal(helpers.normalize_tags(''), [])
    assert_equal(helpers.normalize_tags(','), [])
    assert_equal(helpers.normalize_tags('cool'), ['cool'])
    assert_equal(helpers.normalize_tags('cool,cool'), ['cool'])
    assert_equal(helpers.normalize_tags('cool, cooler'), ['cool', 'cooler'])
    assert_equal(helpers.normalize_tags('cool, cooler '), ['cool', 'cooler'])
    assert_equal(helpers.normalize_tags('cool, cooler ,'), ['cool', 'cooler'])
    assert_equal(helpers.normalize_tags('cool, cooler ,  '), ['cool', 'cooler'])
    assert_equal(
        helpers.normalize_tags(',cool, cooler ,  '), ['cool', 'cooler'])
    assert_equal(
        helpers.normalize_tags(' ,cool, cooler ,,  '), ['cool', 'cooler'])
    assert_equal(
        helpers.normalize_tags("django, franz und bertha,vil/bil"),
        ['django','franz-und-bertha','vil-bil'])

