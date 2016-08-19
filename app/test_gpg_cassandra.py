#!/usr/bin/env python
# Copyright line goes here
"""
Testing for gpg_cassandra.py
This is by no means a complete set of testing, and this is intended at the functional level connecting to a
   live cassandra instance
Unit tests and complete testing (more negative test cases, etc) are still needed
"""

__author__ = "GGibson"

import random
import string
import unittest
import uuid
import logging

from gpg_cassandra import User, UserIdError, UpdateUserError
import gpg_setup_logger

module = __name__
users_keyspace_name = 'users'

log_file_name, module = gpg_setup_logger.create_log_file_name_and_module(__file__, __package__)
gpg_setup_logger.setup_logger('/var/log/gpg', log_file_name, module=module, log_level=logging.DEBUG,
                          use_console_logger=False)
logger = logging.getLogger(module)


def return_random_string(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))


class VerifyUserIdAndNameNotExist(unittest.TestCase):
    """_verify_user_id_and_name_not_exist"""

    def test_verify_existing_user_name_already_exists(self):
        """_verify_user_id_and_name_not_exist - existing name"""
        my_user = User(name='testUser1')
        with self.assertRaises(UserIdError):
            my_user._verify_user_id_and_name_not_exist()

    def test_verify_existing_user_id_already_exists(self):
        """_verify_user_id_and_name_not_exist existing id"""
        my_user = User(user_id='f5c54eea-a9e8-4f81-898e-b965675f46b4', name='smithers')
        with self.assertRaises(UserIdError):
            my_user._verify_user_id_and_name_not_exist()

    def test_verify_non_existing_user_works(self):
        """_verify_user_id_and_name_not_exist - new user"""
        my_user = User(user_id='f5c54eea-a9e8-4f81-898e-b3a5675f6fa4', name='non_existing_user')
        my_user._verify_user_id_and_name_not_exist()
        # it worked if we didn't get an exception!


class GetAllUsers(unittest.TestCase):
    """"get_all_users"""

    def test_get_all_users(self):
        """count"""
        all_users = User.get_all_users().items()
        for k, v in all_users:
            print('{0} - {1}'.format(k, v))
        self.assertGreaterEqual(len(all_users), 3)


class CreateUser(unittest.TestCase):
    """create_user"""

    def test_create_user(self):
        """create_user - new"""
        u_name = return_random_string(7)
        my_user = User(name=u_name, description='user account for {0}'.format(u_name), owner='Bob Hope',
                        owner_email='bob.hope@funny.com', is_domain=True, domain='funny.man')
        my_user.create_user()
        second_user = User(name=u_name)
        self.assertIsNotNone(second_user.return_user_id_by_name())
        # if we got here it worked!

    def test_create_user_alerady_exists(self):
        """create_user - existing"""
        u_name = 'testUser1'
        my_user = User(name=u_name, description='user account for {0}'.format(u_name), owner='Bob Hope',
                        owner_email='bob.hope@funny.com', is_domain=True, domain='funny.man')
        with self.assertRaises(UserIdError):
            my_user.create_user()


class ReturnUserIdByName(unittest.TestCase):
    """return_user_id_by_name"""

    def test_return_user_id_by_name(self):
        """return_user_id_by_name - existing user"""
        my_user = User(name='testUser1')
        self.assertEqual(uuid.UUID('f5c54eea-a9e8-4f81-898e-b965675f46b4'), my_user.return_user_id_by_name())

    def test_return_user_id_by_name_non_existing(self):
        """return_user_id_by_name - non existing user"""
        my_user = User(name='testUser4')
        self.assertIsNone(my_user.return_user_id_by_name())


class UpdateUser(unittest.TestCase):
    """update_user"""

    def test_update_user_existing(self):
        """update_user - existing user"""
        u_name = return_random_string(7)
        my_user = User(name=u_name, description='user account for {0}'.format(u_name), owner='Bob Hope',
                       owner_email='bob.hope@funny.com', is_domain=True, domain='funny.man')
        my_user.create_user()
        new_user = User(name=my_user.name, domain='newDomain')
        new_user.update_user()

    def test_update_user_non_existing_user(self):
        """update_user - non existing user"""
        my_user = User(name=return_random_string(8), domain='newDomain')
        with self.assertRaises(UserIdError):
            my_user.update_user()

    def test_update_user_no_updates(self):
        """update_user - no updates to make"""
        u_name = return_random_string(7)
        my_user = User(name=u_name, description='user account for {0}'.format(u_name), owner='Bob Hope',
                       owner_email='bob.hope@funny.com', is_domain=True, domain='funny.man')
        my_user.create_user()
        new_user = User(name=my_user.name)
        with self.assertRaises(UpdateUserError):
            new_user.update_user()


class GetUserDetails(unittest.TestCase):
    """get_user_details"""

    def test_get_user_details(self):
        """test_get_user_details - existing user"""
        my_user = User(name='testUser1')
        my_user.get_user_details()
        self.assertEquals(my_user.user_id, uuid.UUID('f5c54eea-a9e8-4f81-898e-b965675f46b4'))
        self.assertEquals(my_user.domain, 'wp.fsi')

    def tests_get_user_details_non_existing(self):
        """test_get_user_details - non existing user"""
        my_user = User(name='nonUser')
        with self.assertRaises(UserIdError):
            my_user.get_user_details()


class DeleteUser(unittest.TestCase):
    """delete_user"""

    def test_delete_user(self):
        """delete_user - existing user"""
        u_name = return_random_string(7)
        my_user = User(name=u_name, description='user account for {0}'.format(u_name), owner='Bob Hope',
                       owner_email='bob.hope@funny.com', is_domain=True, domain='funny.man')
        my_user.create_user()
        new_user = User(name=u_name)
        new_user.delete_user()

    def test_delete_user_non_existing(self):
        """delete_user - non existing user"""
        my_user = User(name=return_random_string(9))
        with self.assertRaises(UserIdError):
            my_user.delete_user()


class SetUserId(unittest.TestCase):
    """_set_user_id"""

    def test_set_user_id(self):
        """_set_user_id - existing user"""
        my_user = User(name='testUser1')
        my_user._set_user_id()
        self.assertEquals(my_user.user_id, uuid.UUID('f5c54eea-a9e8-4f81-898e-b965675f46b4'))

    def test_set_user_id_already_set(self):
        """_set_user_id - id already set"""
        my_user = User(name='testUser1', user_id='f5c54eea-a9e8-4f81-898e-b965675f46b4')
        my_user._set_user_id()
        self.assertEquals(my_user.user_id, uuid.UUID('f5c54eea-a9e8-4f81-898e-b965675f46b4'))

    def test_set_user_id_id_and_name_null(self):
        """_set_user_id - user and id null"""
        my_user = User(description='bobs account', owner='bob hope')
        with self.assertRaises(UserIdError):
            my_user._set_user_id()