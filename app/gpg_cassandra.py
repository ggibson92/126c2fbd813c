#!/usr/bin/env python
# Copyright line goes here
"""
Contains the environment classes
"""

__author__ = "GGibson"


import logging
import os
import uuid

from gpg_cassandra_utility import get_connection

logger = logging.getLogger(__name__)


class UserExceptions(Exception):
    pass


class CreateUserError(UserExceptions):
    pass


class UpdateUserError(UserExceptions):
    pass


class UserIdError(UserExceptions):
    pass


class CassandraConnectionError(UserExceptions):
    pass


class User(object):
    KEYSPACE = 'users'
    USERS_TABLE = '{0}.users_tbl'.format(KEYSPACE)

    def __init__(self, user_id=None, name=None, description=None, owner=None, owner_email=None, notes=None,
                 is_domain=None, domain=None):
        """
        :raise: UserIdError: if the user_id is set but not a uuid or convertible to a uuid
        """
        self.name = name
        if not user_id or isinstance(user_id, uuid.UUID):
            self.user_id = user_id
        else:
            try:
                self.user_id = uuid.UUID(user_id)
            except ValueError:
                message = 'cannot load user id: "%s" as it is not a valid uuid', user_id
                logger.error(message)
                raise UserIdError(message)
        self.description = description
        self.owner = owner
        self.owner_email = owner_email
        self.notes = notes
        self.is_domain = is_domain
        self.domain = domain
        self.cassandra = Cassandra()

    def return_user_id(self):
        """interface to return user id"""
        return self.user_id

    def return_user_id_by_name(self):
        """
        return the user id from the user name.  This will limit to the first user with the user name found
        :return: id of the user
        :rtype: uuid
        """
        logger.debug('entering return user id from user name: "%s"', self.name)
        self.user_id = None
        for user in self.cassandra.run_cassandra_cql_command(self._return_user_id_by_name_command()):
            self.user_id = user.id
            break
        logger.debug('returning user id: "%s" for user name: "%s"', self.user_id, self.name)
        return self.user_id

    def create_user(self):
        """
        creates a user
        """
        logger.debug('entering create user: "%s"', self.name)
        self._verify_user_id_and_name_not_exist()
        self.cassandra.run_cassandra_cql_command(self._return_create_user_command())
        self._set_user_id()
        logger.debug('successfully created user: "%s"', self.name)

    def update_user(self):
        """
        update a user based on id.  If the id value isn't set, it will lookup based on name
        """
        logger.debug('entering update user: "%s"', self.name)
        self._set_user_id()
        self.cassandra.run_cassandra_cql_command(self._return_update_user_command())
        logger.debug('successfully updated user: "%s"', self.name)

    def get_user_details(self):
        """
        get user details based on id.  If the id value isn't set, it will lookup based on name
        """
        logger.debug('entering get user detail: "%s"', self.name)
        self._set_user_id()
        self.cassandra.run_cassandra_cql_command(self._return_user_details_command())

        for user in self.cassandra.run_cassandra_cql_command(self._return_user_details_command()):
            self.name = user.name
            self.description = user.description
            self.owner = user.owner
            self.owner_email = user.owner_email
            self.notes = user.notes
            self.is_domain = user.is_domain
            self.domain = user.domain
            break
        logger.debug('successfully updated user: %s', self)

    @staticmethod
    def get_all_users():
        """
        Returns a dictionary of all users and their ids
        :return dictionary of users and ids
        :rtype: dictionary, key: id, value: name
        """
        logger.debug('entering return all users and ids')
        users = {}
        for user in Cassandra().run_cassandra_cql_command(User._return_users_command()):
            logger.debug('adding user: "%s", id: "%s"', user.id, user.name)
            users[user.name] = str(user.id)
        logger.debug('returning: %d users', len(users))
        return users

    def delete_user(self):
        """
        delete a user based on id.  If the id value isn't set, it will lookup based on name
        """
        logger.debug('entering delete user: "%s"', self.name)
        self._set_user_id()
        self.cassandra.run_cassandra_cql_command(self._return_delete_user_command())
        logger.debug('successfully deleted user: "%s"', self.name)

    def _set_user_id(self):
        """
        if user_id is not set lookup by name
        :raise UserIdError if user_id and name are not defined
        """
        logger.debug('entering set user id')
        if self.user_id:
            logger.debug('user id: %s is already set, return it', self.user_id)
            return self.user_id
        if not self.name:
            message = 'cannot set user id when both user id and name are not defined'
            logger.error(message)
            raise UserIdError(message)
        self.return_user_id_by_name()
        if not self.user_id:
            message = 'failed to find the user id for user: "{0}"'.format(self.name)
            logger.error(message)
            raise UserIdError(message)
        logger.debug('set user id: %s from user name: "%s"', self.user_id, self.name)

    def _verify_user_id_and_name_not_exist(self):
        """
        verifies the user id and user name do not already exist in the database
        :raise UserIdError if user_id and name are not defined OR the user already exists (id and/or name
        """
        logger.debug('entering verify user id and name do not exist in the database')
        if not self.name and not self.user_id:
            message = 'cannot check user when both user id and name are not defined'
            logger.error(message)
            raise UserIdError(message)
        if self.name:
            for user in self.cassandra.run_cassandra_cql_command(self._return_verify_user_name_not_exist_command()):
                message = 'Failed, a user already exists that matches the name: {0}'.format(self.name)
                logger.error(message)
                raise UserIdError(message)
        if self.user_id:
            for user in self.cassandra.run_cassandra_cql_command(self._return_verify_user_id_not_exist_command()):
                message = 'Failed, a user already exists that matches the id: {0}'.format(self.user_id)
                logger.error(message)
                raise UserIdError(message)
        logger.debug('completed verifying user id and name do not exist in the database')

    def _return_create_user_command(self):
        """
        returns the CQL command to create a user
        :return: cql command
        :rtype: string
        """
        self._set_value_defaults()
        command = "INSERT INTO {0} (id, name, description, owner, owner_email, notes, is_domain, domain) " \
                  "VALUES ({1}, '{2}', '{3}', '{4}', '{5}', '{6}', {7}, '{8}');".format(User.USERS_TABLE,
                                                                                        self.user_id, self.name,
                                                                                        self.description, self.owner,
                                                                                        self.owner_email, self.notes,
                                                                                        self.is_domain, self.domain)
        print(command)
        logger.debug('create user CQL command: "%s"', command)
        return command

    def _return_update_user_command(self):
        """
        returns the CQL command to update a user.  All fields can be changed except id and name
        :return: cql create command
        :rtype: string
        """
        columns_to_update = []
        if self.description:
            columns_to_update.append("description='{0}'".format(self.description))
        if self.owner:
            columns_to_update.append("owner='{0}'".format(self.owner))
        if self.owner_email:
            columns_to_update.append("owner_email='{0}'".format(self.owner_email))
        if self.notes:
            columns_to_update.append("notes='{0}'".format(self.notes))
        if self.is_domain:
            columns_to_update.append("is_domain={0}".format(self.is_domain))
        if self.domain:
            columns_to_update.append("domain='{0}'".format(self.domain))

        if not columns_to_update:
            raise UpdateUserError('No columns to update')

        command = "UPDATE {0} SET {1} WHERE id={2};".format(User.USERS_TABLE, ', '.join(columns_to_update),
                                                            self.user_id)
        print('---------')
        print(command)
        logger.debug('update user CQL command: "%s"', command)
        return command

    def _return_delete_user_command(self):
        """
        returns the CQL command to delete a user
        :return: cql command
        :rtype: string
        """
        command = "DELETE FROM {0} WHERE id={1};".format(User.USERS_TABLE, self.user_id)
        logger.debug('delete user CQL command: "%s"', command)
        return command

    def _return_user_id_by_name_command(self):
        """
        returns the CQL command to select a user name by user_id
        :return: cql command
        :rtype: string
        """
        command = "SELECT id FROM {0} WHERE name='{1}';".format(User.USERS_TABLE, self.name)
        logger.debug('user by name CQL command: "%s"', command)
        return command

    def _return_user_details_command(self):
        """
        returns the CQL command to select user data
        :return: cql command
        :rtype: string
        """
        command = "SELECT * FROM {0} WHERE id={1}".format(User.USERS_TABLE, self.user_id)
        logger.debug('select all users CQL command: "%s"', command)
        return command

    @staticmethod
    def _return_users_command():
        """
        returns the CQL command to select all user data
        :return: cql command
        :rtype: string
        """
        command = "SELECT id, name FROM {0}".format(User.USERS_TABLE)
        logger.debug('select user details CQL command: "%s"', command)
        return command

    def _return_verify_user_name_not_exist_command(self):
        """
        returns the CQL command to verify user name does not exist
        :return: cql command
        :rtype: string
        """
        if not self.name:
            logger.debug('user name not defined, return None')
            return None
        command = "SELECT id FROM {0} WHERE name = '{1}'".format(User.USERS_TABLE, self.name)
        print(command)
        logger.debug('verify user name does not exist CQL command: "%s"', command)
        return command

    def _return_verify_user_id_not_exist_command(self):
        """
        returns the CQL command to verify user id does not exist
        :return: cql command
        :rtype: string
        """
        if not self.user_id:
            logger.debug('user id not defined, return None')
            return None
        command = "SELECT id FROM {0} WHERE id = {1}".format(User.USERS_TABLE, self.user_id)
        print(command)
        logger.debug('verify user id does not exist CQL command: "%s"', command)
        return command

    def _set_value_defaults(self):
        """
        Updates the defaults from None if values are not set
        :raise: CreateUserError if name is not set
        """
        logger.debug('entering set value defaults')
        if not self.name:
            raise UserExceptions('Cannot create user without user name')
        if not self.user_id:
            self.user_id = uuid.uuid4()
        if not self.description:
            self.description = ''
        if not self.owner:
            self.owner = ''
        if not self.owner_email:
            self.owner_email = ''
        if not self.notes:
            self.notes = ''
        if not self.is_domain:
            self.is_domain = False
        if not self.domain:
            self.domain = ''
        logger.debug('completed setting value defaults')

    def __str__(self):
        return 'user id: {0}, name: "{1}", description: "{2}", owner: "{3}", owner email: "{4}", notes: "{5}", ' \
               'is domain user: {6}, domain: "{7}"'.format(self.user_id, self.name, self.description, self.owner,
                                                           self.owner_email, self.notes, self.is_domain, self.domain)

    def return_json(self):
        json_dict = self.__dict__
        del json_dict['cassandra']
        json_dict['user_id'] = str(json_dict['user_id'])
        return json_dict


class Cassandra(object):
    def __init__(self, contact_points=None, port=9042, keyspace='users'):
        if not contact_points:
            try:
                contact_points_string = os.environ['contact_points']
                logger.debug('contact points string: "%s"', contact_points_string)
                contact_points = contact_points_string.split(',')
                logger.debug('contact points list: "%s"', contact_points)
            except KeyError:
                message = 'cannot connect to Cassandra as no contact_points have been provided'
                logger.exception(message)
                raise CassandraConnectionError(message)
            except AttributeError:
                message = 'cannot connect to Cassandra as contact points provided cannot be parsed'
                logger.exception(message)
                raise CassandraConnectionError(message)
        else:
            logger.debug('contact points is set as: "%s"', contact_points)

        self.contact_points = contact_points
        self.port = port
        self.keyspace = keyspace

    def run_cassandra_cql_command(self, command):
        """
        Runs a Cassandra CQL command
        :param: command: command to run
        :return: result set from the cql command
        :rtype: Cassandra ResultSet
        """
        return_result = None
        with get_connection(contact_points=self.contact_points, keyspace=self.keyspace, port=self.port) \
                as (cluster, session):
            logger.debug('running Cassandra cql command: "%s", keyspace: "%s", port: "%s", contact points: "%s"',
                         command, self.keyspace, self.port, self.contact_points)
            return_result = session.execute(command)
            logger.debug('successfully ran Cassandra cql command: "%s"', command)
        return return_result