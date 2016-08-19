#!/usr/bin/env python
# Copyright line goes here

__author__ = "GGibson"

from flask import Flask
import os

app = Flask(__name__)
from app import gpg_views
