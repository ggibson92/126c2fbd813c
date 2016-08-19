#!/usr/bin/env python
# Copyright line goes here
"""
Cassandra utility functions
"""

__author__ = "GGibson"

from cassandra.cluster import Cluster
import contextlib
import logging

module = __name__

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def get_connection(contact_points=None, keyspace=None, port=9042):
    """
    Creates/destroys a database connection
    :rtype: (Cluster, Session)
    """
    logger.info("Connecting using contact_points=%s", contact_points)
    cluster = Cluster(contact_points=contact_points, port=port)
    session = cluster.connect(keyspace)
    try:
        yield (cluster, session)
    finally:
        if session and not session.is_shutdown:
            logger.debug('shutting down connection')
            session.cluster.shutdown()
