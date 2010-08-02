import unittest
import datetime

from simblin import create_app, helpers

class PasswordTestCase(unittest.TestCase):
    
    def test_password_functions(self):
        """Check the integrity of the password functions"""
        raw_password = 'passworD546$!!.,.'
        hash = helpers.set_password(raw_password)
        self.assertTrue(helpers.check_password(raw_password, hash))
        self.assertFalse(helpers.check_password('abc', hash))
        
        
class NormalizeTestCase(unittest.TestCase):
    
    def test_slug_normalizing(self):
        self.assertEqual(helpers.normalize(''), '')
        self.assertEqual(helpers.normalize('dadada'), 'dadada')
        self.assertEqual(helpers.normalize('DaDaDa'), 'dadada')
        self.assertEqual(helpers.normalize('The house'), 'the-house')
        self.assertEqual(helpers.normalize('The  house'), 'the-house')
        self.assertEqual(helpers.normalize(' 123-name '), '123-name')
        # TODO: test special symbols like ? & = <> /
    
    def test_tags_normalizing(self):
        """
        Test the correct interpretation of a string of comma separated tags
        """
        self.assertEqual(helpers.normalize_tags(''), [])
        self.assertEqual(helpers.normalize_tags(','), [])
        self.assertEqual(helpers.normalize_tags('cool'), ['cool'])
        self.assertEqual(helpers.normalize_tags('cool,cool'), ['cool'])
        self.assertEqual(
            helpers.normalize_tags('cool, cooler'), ['cool', 'cooler'])
        self.assertEqual(
            helpers.normalize_tags('cool, cooler '), ['cool', 'cooler'])
        self.assertEqual(
            helpers.normalize_tags('cool, cooler ,'), ['cool', 'cooler'])
        self.assertEqual(
            helpers.normalize_tags('cool, cooler ,  '), ['cool', 'cooler'])
        self.assertEqual(
            helpers.normalize_tags(',cool, cooler ,  '), ['cool', 'cooler'])
        self.assertEqual(
            helpers.normalize_tags(' ,cool, cooler ,,  '), ['cool', 'cooler'])
        self.assertEqual(
            helpers.normalize_tags("django, franz und bertha,vil/bil"),
            ['django','franz-und-bertha','vil-bil'])
