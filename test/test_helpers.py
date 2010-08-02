from nose.tools import assert_equal, assert_true, assert_false, with_setup
from simblin import helpers


def test_password_functions():
    """Check the integrity of the password functions"""
    raw_password = 'passworD546$!!.,.'
    hash = helpers.set_password(raw_password)
    assert_true(helpers.check_password(raw_password, hash))
    assert_false(helpers.check_password('abc', hash))
    
            
def test_slug_normalizing():
    assert_equal(helpers.normalize(''), '')
    assert_equal(helpers.normalize('dadada'), 'dadada')
    assert_equal(helpers.normalize('DaDaDa'), 'dadada')
    assert_equal(helpers.normalize('The house'), 'the-house')
    assert_equal(helpers.normalize('The  house'), 'the-house')
    assert_equal(helpers.normalize(' 123-name '), '123-name')
    # TODO: test special symbols like ? & = <> /
    
    
def test_tags_normalizing():
    """
    Test the correct interpretation of a string of comma separated tags
    """
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
