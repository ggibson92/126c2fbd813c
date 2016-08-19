#!/usr/bin/env python
# Copyright line goes here
"""
The Flask (Rest) API code for users
"""

__author__ = "GGibson"


from flask import request, jsonify, make_response, Response
import logging
from operator import methodcaller

from app import app
import gpg_cassandra
import json
import gpg_setup_logger

module = __name__
log_file_name, module = gpg_setup_logger.create_log_file_name_and_module(__file__, __package__)
gpg_setup_logger.setup_logger('/var/log/gpg', log_file_name, module=module, log_level=logging.DEBUG,
                              use_console_logger=False)
global logger
logger = logging.getLogger(module)

@app.route('/')
@app.route('/index')
def index():
    calls = """
    GET /users - returns all users
    GET /user/<user_name> - return user details
    POST /user - create user
    PUT /user/<user_name> - update user
    DELETE /user/<user_name> - delete user

    sample user values (create user and update user):
    {
    	"name": "user_name",
    	"description": "user_description",
    	"owner": "owner_name",
    	"owner_email": "owner@email.com",
    	"notes": "user_notes",
    	"is_domain": true,
    	"domain": "user.domain.name"
    }
    """
    return calls


def return_all_users():
    u = (gpg_cassandra.User.get_all_users())
    return_json = {'users': u}
    logger.info('calling [%s] %s', request.method, request.path)
    logger.debug('completed [%s] %s, response: %s', request.method, request.path, return_json)
    return jsonify(**return_json)


def return_user_detail(user_object):
    user_object.get_user_details()
    return Response(json.dumps(user_object, default=methodcaller("return_json"), indent=4, sort_keys=True),
                    status=200, mimetype='application/json')


def create_user():
    logger.info('calling [%s] %s', request.method, request.path)
    if request.method == 'POST':
        if request.mimetype != 'application/json':
            return make_response("unsupported request mimetype: {}".format(request.mimetype), 415)
        new_user = gpg_cassandra.User(**json.loads(request.data))
        if ' ' in new_user.name:
            return make_response("user name cannot have a space in it: {}".format(new_user.name), 400)
        new_user.create_user()
        new_user.get_user_details()
        logger.debug('completed [%s] %s')
        return Response(json.dumps(new_user, default=methodcaller("return_json"), indent=4, sort_keys=True),
                        status=201, mimetype='application/json')


def delete_user(user_object):
    user_object.delete_user()
    return Response('', status=200, mimetype='application/json')


def update_user(user_name):
    if request.mimetype != 'application/json':
        return make_response("unsupported request mimetype: {}".format(request.mimetype), 415)
    user = gpg_cassandra.User(**json.loads(request.data))
    user.name = user_name
    user.update_user()
    user.get_user_details()
    return Response(json.dumps(user, default=methodcaller("return_json"), indent=4, sort_keys=True),
                    status=200, mimetype='application/json')


@app.route('/users', methods=['GET'])
def flask_users():
    """
    return a json list of all user ids and names
    """
    return return_all_users()


@app.route('/user', methods=['POST'])
def flask_user():
    """
    create a user
    """
    return create_user()


@app.route('/user/<user_name>', methods=['GET', 'PUT', 'DELETE'])
def flask_update_user(user_name):
    """
    return a json list of user details, update user, delete user
    """
    # verify the user id exists
    user_object = gpg_cassandra.User(name=user_name)
    user_object.return_user_id_by_name()
    if not user_object.user_id:
        return make_response('user: {0} does not exist'.format(user_name), 400)
    if request.method == 'GET':
        return return_user_detail(user_object)
    if request.method == 'PUT':
        return update_user(user_name)
    if request.method == 'DELETE':
        return delete_user(user_object)
