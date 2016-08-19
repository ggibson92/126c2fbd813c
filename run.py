#!/usr/bin/env python
# Copyright line goes here
"""
Run script for the Flask Application
"""

__author__ = "GGibson"

from app import app
app.run(host='0.0.0.0', debug=True) # needed for docker
#app.run(host='127.0.0.1', debug=True) # local
