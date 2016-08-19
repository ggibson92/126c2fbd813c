#!/usr/bin/env python
# Copyright line goes here
"""
users code that reads and writes to json file
This code is not actually used, originally I wasn't sure I was going to create the backend so I started creating a
    json backend (this).  I wanted to share this code I wrote for this project as it shows reading and writing from
    json to classes (serialization / deserialization), class enheritance, etc.  Please note, I didn't fully test this
    code as I replaced it when I was about 90% done
"""


__author__ = "GGibson"

import datetime
import json
import logging
from operator import attrgetter, methodcaller
import os
import uuid


logger = logging.getLogger(__name__)
user_conf_file = '/tmp/users.json'


class GpgUserExceptions(Exception):
    pass


class UserNameError(GpgUserExceptions):
    pass


class HostnameError(GpgUserExceptions):
    pass


class DomainNameError(GpgUserExceptions):
    pass


class UserJsonDocError(GpgUserExceptions):
    pass


class RemoveUserError(GpgUserExceptions):
    pass


class Users(object):
    """
    Class to contain the users information for creating the users document
    """
    def __init__(self, users=None, date_created=None, date_modified=None):
        if date_created:
            self.date_created = date_created
        else:
            self.date_created = str(datetime.datetime.now())

        if date_modified:
            self.date_modified = date_modified
        else:
            self.date_modified = self.date_created

        if users:
            self.users = users
        else:
            self.users = []

    def add_user(self, user):
        """
        Adds a user to the users list
        :param: user (User) either DomainUser or LocalUser
        :return: None
        """
        logger.debug('adding user: %s to users list', user)
        if user in self.users:
            logger.warning('cannot add user: "%s" to users list as user already exists', user)
        self.users.append(user)
        logger.info('successfully added user: %s to users list', user)

    def return_user_by_uuid(self, user_uuid):
        """
        Returns a user based on the user uuid
        :param: user_uuid (str)
        :return User (UserAccount)
        :raise UserNameError: if we fail to find the user for any reason
        """
        logger.debug('entering return user with uuid: "%s"', user_uuid)
        if not user_uuid:
            message = 'cannot find user by uuid as the uuid to remove was not provided'
            logger.error(message)
            raise UserNameError(message)
        for user in self.users:
            if user.user_uuid == user_uuid:
                logger.debug('found user: %s', user)
                return user
        message = 'Failed to find user with uuid: "{0}"'.format(user_uuid)
        logger.error(message)
        raise UserNameError(message)

    def return_domain_user_by_name(self, user_name, domain_name):
        """
        Return a user from the users list based on user name and domain name
        :param: user_name (str)
        :param: domain_name (str)
        :return User (UserAccount)
        :raise UserNameError: if user_name or domain name is empty or None, or we don't find the user
        """
        logger.debug('entering return user: "%s", domain name: "%s"', user_name, domain_name)
        # verify params are good
        error_message = None
        if not user_name:
            error_message = 'cannot return user by name as the user name was not provided'
        elif not domain_name:
            error_message = 'Cannot return user: "{0}" as the domain name was not provided'
        if error_message:
            logger.error(error_message)
            raise UserNameError(error_message)

        for user in self.users:
            if user.user_type == DomainUser.TYPE and user.name == user_name:
                if hasattr(user, 'domain_name'):
                    if domain_name == user.domain_name:
                        logger.debug('found user: %s', user)
                        return user
                else:
                    logger.warning('Failed to find the domain_name attribute for the domain user')

        message = 'Failed to find user: "{0}", domain: "{1}"'.format(user_name, domain_name)
        logger.error(message)
        raise UserNameError(message)

    def return_local_user_by_name(self, user_name, hostname):
        """
        Returns a user from the users list based on user name and hostname name
        :param: user_name (str)
        :param: hostname (str)
        :return None
        :raise UserNameError: if user_name or hostname is empty or None, or we fail to find the user
        """
        logger.debug('entering return user: "%s", hostname: "%s"', user_name, hostname)
        # verify params are good
        error_message = None
        if not user_name:
            error_message = 'cannot return user by name as the user name was not provided'
        elif not hostname:
            error_message = 'Cannot return user: "{0}" as the hostname was not provided'
        if error_message:
            logger.error(error_message)
            raise UserNameError(error_message)

        for user in self.users:
            if user.type == LocalUser.TYPE and user.name == user_name:
                if hasattr(user, 'hostname'):
                    if hostname == user.hostname:
                        logger.debug('returning user: %s', user)
                        return user
                else:
                    logger.warning('Failed to find the hostname attribute for the local user')

        message = 'Failed to find user: "{0}", hostname: "{1}"'.format(user_name, hostname)
        logger.error(message)
        raise UserNameError(message)

    def remove_user_by_uuid(self, user_uuid):
        """
        Removes a user from the users list based on user uuid
        :param: user_uuid (str)
        :return None
        :raise RemoveUserError: if we fail to remove the user for any reason
        """
        logger.debug('entering remove user with uuid: "%s"', user_uuid)
        self._remove_user(self.return_user_by_uuid(user_uuid))
        logger.info('successfully removed user with uuid: "%s"', user_uuid)

    def remove_domain_user_by_name(self, user_name, domain_name):
        """
        Removes a user from the users list based on user name and domain name
        :param: user_name (str)
        :param: domain_name (str)
        :return None
        :raise UserNameError: if user_name or domain name is empty or None
        :raise RemoveUserError: if we fail to remove the user
        """
        logger.debug('entering remove user: "%s", domain name: "%s"', user_name, domain_name)
        try:
            self._remove_user(self.return_domain_user_by_name(user_name, domain_name))
        except UserNameError:
            raise RemoveUserError
        logger.info('successfully removed user: "%s", domain name: "%s"', user_name, domain_name)

    def remove_local_user_by_name(self, user_name, hostname):
        """
        Removes a user from the users list based on user name and hostname name
        :param: user_name (str)
        :param: hostname (str)
        :return None
        :raise UserNameError: if user_name or hostname is empty or None
        :raise RemoveUserError: if we fail to remove the user
        """
        logger.debug('entering remove user: "%s", hostname: "%s"', user_name, hostname)
        try:
            self._remove_user(self.return_local_user_by_name(user_name, hostname))
        except UserNameError:
            raise RemoveUserError
        logger.info('successfully removed user: "%s", hostname: "%s"', user_name, hostname)

    def _remove_user(self, user):
        """
        Removes a user from the users list
        :param: user (UserAccount)
        :return None
        :raise RemoveUserError: if we fail to remove the user
        """
        logger.debug('entering remove user: "%s"', user)
        error_message = None
        if not user:
            error_message = 'user not defined, cannot remove user'
        if not isinstance(user, UserAccount):
            error_message = 'user param is not of UserAccount type, cannot remove user'
        if error_message:
            logger.error(error_message)
            raise RemoveUserError(error_message)
        try:
            self.users.remove(user)
        except ValueError:
            message = 'failed to remove user: {0}'.format(user)
            logger.exception(message)
            raise RemoveUserError(message)
        logger.info('successfully removed user: "%s"', user)

    def return_user_names(self):
        """
        Returns a list of user names
        :rtype: List(str)
        """
        logger.debug('return list of user names')
        return map(attrgetter('name'), self.users)

    def load_users(self):
        """
        Loads the users from the user conf file
        """
        logger.debug('entering load users conf (json) file: "%s"', user_conf_file)
        self.users = []
        users_doc = _load_json_document(user_conf_file)
        if not users_doc:
            message = 'failed to load user conf (json) file: "{0}"'.format(user_conf_file)
            logger.error(message)
            raise UserJsonDocError(message)
        for user in users_doc['users']:
            self.users.append(UserAccount.return_user_object(user))
        logger.info('loaded users: %s', ', '.join(self.return_user_names()))
        logger.debug('completed loading users conf (json) file: "%s"', user_conf_file)

    def write_users(self):
        logger.debug('entering write users conf file: "%s"', user_conf_file)
        try:
            with open(user_conf_file, 'w') as users_file:
                json.dump(self, users_file, default=methodcaller("return_json"), indent=4)
        except EnvironmentError:
            message = 'failed to create user conf file: "{0}"'.format(user_conf_file)
            logger.exception(message)
            raise UserJsonDocError(message)
        logger.debug('successfully wrote users conf file: "%s"', user_conf_file)

    def create_users(self):
        """
        Creates a sample user conf file
        """
        logger.debug('creating user conf file: "%s"', user_conf_file)
        #users_list = []
        self.users.append(DomainUser('bobHopeTestUser', 'wp', 'An account for Bob', 'Bob Hope', 'bobHope@bobby.com',
                                     'a temp account for testing'))
        self.users.append(DomainUser('bobHopeTestAdmin', 'wp', 'An admin account for Bob', 'Bob Hope',
                                     'bobHope@bobby.com', 'a temp account for testing admin rights'))
        self.users.append(LocalUser('smithers', 'smithers-lt', 'Smithers local user account for his laptop', 'Smithers',
                                    'smithers@someone.com', 'smithers local account'))
        self.write_users()
        logger.info('successfully created user conf file: "%s"', user_conf_file)

    def return_json(self):
        return self.__dict__


class UserAccount(object):
    """base class for user accounts"""
    def __init__(self, name, description, owner, owner_email, notes, user_type, user_uuid=None):
        self.name = name
        self.description = description
        self.owner = owner
        self.owner_email = owner_email
        self.notes = notes
        self.user_type = user_type
        if user_uuid:
            self.user_uuid = user_uuid
        else:
            self.user_uuid = self._return_uuid()

    @staticmethod
    def return_user_object(user):
        """
        Returns the UserAccount sub class object for the specified user
        :param: user: user in Json
        :rtype: UserAccount sub class
        :return: UserAccount (sub class)
        """
        logger.debug('entering return user object: "%s"', user)
        if 'user_type' not in user:
            message = 'Failed to find user_type for user: "{0}"'.format(user)
            logger.error(message)
            raise UserJsonDocError(message)

        if user['user_type'] == DomainUser.TYPE:
            logger.debug('user type: %s', DomainUser.TYPE)
            user_to_return = DomainUser(**user)
        elif user['user_type'] == LocalUser.TYPE:
            logger.debug('user type: %s', LocalUser.TYPE)
            user_to_return = LocalUser(**user)
        else:
            message = 'The user type: "{0}" is unknown for user object: "{1}"'.format(user['user_type'], user)
            logger.error(message)
            raise UserJsonDocError(message)

        logger.debug('returning user object: "%s", returning: "%s"', user, user_to_return)
        return user_to_return

    @staticmethod
    def _return_uuid():
        """Returns a UUID"""
        logger.debug('generating user uuid')
        return str(uuid.uuid4())

    def verify_user_provided(self):
        """
        Verifies the user name field is set
        :raise UserNameError if the user name is not set
        """
        logger.debug('entering verify user name is set for user: "%s"', self)
        if not self.name:
            message = 'user name cannot be null'
            logger.error(message)
            raise UserNameError(message)
        logger.debug('completed verifying user name is set for user: "%s"', self)

    def return_login_name(self):
        """
        Returns the user login sting
        Not implemented for the the UserAccount (parent) class, must be called from the sub class
        """
        raise NotImplementedError('return login name must be implemented on the child class')

    def return_login_hash(self, system_id):
        """
        Returns the login hash for a user based on a specific system_id
        :param: system_id (str): this is the system ID to create the hash for (typically a uuid)
        :return: uuid-system_id
        :rtype: str
        """
        logger.debug('entering return login hash for system id: "%s", user: %s', system_id, self.name)
        login_hash = '{0}-{1}'.format(self.user_uuid, system_id)
        logger.debug('returning login hash: "%s" for system id: "%s", user: %s', login_hash, system_id, self.name)
        return login_hash

    def __str__(self):
        return '{0}-{1}'.format(self.name, self.user_uuid)

    def __repr__(self):
        return 'name: {0} description: {1} owner: {2} owner email: {3} notes: {4} uuid: {5}'.format(
            self.name, self.description, self.owner, self.owner_email, self.notes, self.user_uuid)

    def return_json(self):
        return self.__dict__


class DomainUser(UserAccount):
    TYPE = 'domainUser'

    def __init__(self, name, domain_name, description, owner, owner_email, notes, user_type=None, user_uuid=None):
        super(DomainUser, self).__init__(name, description, owner, owner_email, notes, DomainUser.TYPE, user_uuid)
        self.domain_name = domain_name

    def return_login_name(self):
        """
        Returns the login domain_name\user for local user accounts
        :return: domain_name\user
        :rtype: str
        """
        logger.debug('entering return domain login user name for user: %s', self)
        self.verify_user_provided()
        self.verify_domain_name()
        login = r'{0}\{1}'.format(self.domain_name, self.name)
        logger.debug('return domain user login for user: "%s", uuid: "%s", domain name: "%s", login: "%s" '
                     'for user: %s', self.name, self.user_uuid, self.domain_name, login, self)
        return login

    def verify_domain_name(self):
        """
        Verifies the user domain name field is set
        :raise DomainNameError if the user domain name is not set
        """
        logger.debug('entering verify user domain name is set for user: "%s"', self)
        if not self.domain_name:
            message = 'user domain name cannot be null'
            logger.error(message)
            raise DomainNameError(message)
        logger.debug('completed verifying user domain name is set for user: "%s"', self)

    def __repr__(self):
        return '{0} domain: {1}'.format(super(DomainUser, self).__repr__(), self.domain_name)

    def __str__(self):
        return '{0} domain: {1}'.format(super(DomainUser, self).__str__(), self.domain_name)

    def return_json(self):
        return self.__dict__


class LocalUser(UserAccount):
    TYPE = 'localUser'

    def __init__(self, name, hostname, description, owner, owner_email, notes, user_type=None, user_uuid=None):
        super(LocalUser, self).__init__(name, description, owner, owner_email, notes, LocalUser.TYPE, user_uuid)
        self.hostname = hostname

    def return_login_name(self):
        """
        Returns the login name@hostname for local user accounts
        :return: name@hostname
        :rtype: str
        """
        logger.debug('entering return local login user name for user: %s', self)
        self.verify_user_provided()
        self.verify_hostname()
        login = '{0}@{1}'.format(self.name, self.hostname)
        logger.debug('return local user login for user: "%s", uuid: "%s", hostname: "%s", login: "%s" '
                     'for user: %s', self.name, self.user_uuid, self.hostname, login, self)
        return login

    def verify_hostname(self):
        """
        Verifies the user hostname field is set
        :raise HostnameError if the user hostname is not set
        """
        logger.debug('entering verify user hostname is set for user: "%s"', self)
        if not self.hostname:
            message = 'user hostname cannot be null'
            logger.error(message)
            raise HostnameError(message)
        logger.debug('completed verifying user hostname is set for user: "%s"', self)

    def __repr__(self):
        return '{0} hostname: {1}'.format(super(LocalUser, self).__repr__(), self.hostname)

    def __str__(self):
        return '{0} hostname: {1}'.format(super(LocalUser, self).__str__(), self.hostname)

    def return_json(self):
        return self.__dict__


def _load_json_document(json_file):
    """
    Reads a Json document and returns that object so it can be read
    :param json_file the Json file to load
    :return object containing Json document, if the file is empty, not existing, or has a syntax error returns None
    :Json
    """
    logger.debug('entering load json document from file: "%s"', json_file)
    if not os.path.isfile(json_file):
        logger.error('Json file: "%s" does not exist, cannot load Json document', json_file)
        return None
    else:
        logger.debug('Loaded Json file: "{0}"'.format(json_file))
    try:
        with open(json_file) as fp:
            data = fp.read()
            json_document = json.loads(data.decode('utf-8-sig'))  # will work with or without BOM
    except IOError:
        logger.exception('Failed to read the Json file: "%s"', json_file)
        return None
    except ValueError:
        logger.exception('Failed to parse Json file: "%s"', json_file)
        return None
    logger.debug('completed loading json document from file: "%s", document: %s', json_file, json_document)
    return json_document


def update_user(users, uuid, **kwargs):
    if not uuid:
        print 'very bad'
        import sys
        sys.exit(1)

    user = users.return_domain_user_by_name('bobHopeTestUser', 'wp')
    if 'name' in kwargs:
        print('can not update name, poo')
        import sys
        sys.exit(1)

    if kwargs is not None:
        for key, value in kwargs.iteritems():
            if hasattr(user, key):
                print('Update: "{0}" from: "{1}" to: "{2}"'.format(key, getattr(user, key), value))
                setattr(user, key, value)
            else:
                print('Warning, cannot update attribute: "{0}" as it does not exist', key)
    else:
        print 'no args pass, no update needed'
