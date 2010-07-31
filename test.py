#!/bin/env python
import os
import blog
import unittest
import tempfile

# TODO: Add Test Cases
#       * Expect error (flash) if user tries to register with empty forms

class PasswordTestCase(unittest.TestCase):
    
    def test_password_functions(self):
        raw_password = 'passworD546$!!.,.'
        hash = blog.set_password(raw_password)
        self.assertTrue(blog.check_password(raw_password, hash))
        self.assertFalse(blog.check_password('abc', hash))


class BlogTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, blog.DATABASE = tempfile.mkstemp()
        self.app = blog.app.test_client()
        blog.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(blog.DATABASE)
        

if __name__ == '__main__':
    unittest.main()
