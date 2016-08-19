#!/usr/bin/env python
# Copyright line goes here
"""
Setups up the Cassandra users keyspace
Note: contact_points needs to be updated to if/when the cassandra seeds change
"""

__author__ = "GGibson"

from cassandra import DriverException
from cassandra.protocol import SyntaxException

from gpg_cassandra_utility import get_connection
import logging

import gpg_setup_logger

module = __name__
users_keyspace_name = 'users'
contact_points = ['10.158.15.83', '10.158.15.138']

log_file_name, module = gpg_setup_logger.create_log_file_name_and_module(__file__, __package__)
gpg_setup_logger.setup_logger('/var/log/gpg', log_file_name, module=module, log_level=logging.DEBUG,
                          use_console_logger=False)
logger = logging.getLogger(module)

commands = [
    """CREATE TABLE IF NOT EXISTS users.users_tbl (
    id uuid PRIMARY KEY,
    name text,
    description text,
    owner text,
    owner_email text,
    notes text,
    is_domain boolean,
    domain text,
    ) WITH bloom_filter_fp_chance = 0.01
    AND caching = '{"keys":"ALL", "rows_per_partition":"NONE"}'
    AND comment = ''
    AND compaction = {'min_threshold': '4', 'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy',
    'max_threshold': '32'}
    AND compression = {'sstable_compression': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99.0PERCENTILE';""",
    'create index on users_tbl (name);',
    'create index on users_tbl (owner);',
    'create index on users_tbl (owner_email);',
    """INSERT INTO users.users_tbl (id, name, description, owner, owner_email, notes, is_domain, domain)
    VALUES (f5c54eea-a9e8-4f81-898e-b965675f46b4, 'testUser1', 'a test account for test user 1', 'Tester 1',
      'test1@my.com', 'no notes1', true, 'wp.fsi');""",
    """INSERT INTO users.users_tbl (id, name, description, owner, owner_email, notes, is_domain, domain)
    VALUES (f5d599bb-975f-47d4-ba50-ed965f0d44cb, 'testUser2', 'a test account for test user 2', 'Tester 2',
      'test2@my.com', 'no notes2', false, 'myMac');""",
    """INSERT INTO users.users_tbl (id, name, description, owner, owner_email, notes, is_domain, domain)
    VALUES (5d204d7e-0c08-425d-ac03-cb1fe48c01f8, 'testUser3', 'a test account for test user 3', 'Tester 3',
      'test3@my.com', 'no notes3', true, 'wp.fsi');"""
]

logger.info('setting up "%s" keyspace', users_keyspace_name)
with get_connection(contact_points=contact_points) as (cluster, session):
    logger.debug('drop "%s" keyspace if it exists', users_keyspace_name)
    try:
        session.execute('DROP KEYSPACE IF EXISTS {0}'.format(users_keyspace_name))
    except (SyntaxException, DriverException):
        logger.exception('Failed running drop keyspace: "%s"', users_keyspace_name)
        raise
    logger.debug('create keyspace: "%s"', users_keyspace_name)
    session.execute("CREATE KEYSPACE IF NOT EXISTS {0} WITH REPLICATION = {{'class' : 'SimpleStrategy', 'replication_factor' : 2}};".format(users_keyspace_name))
    session = cluster.connect(users_keyspace_name)

    for command in commands:
        logger.debug('running cql command: {0}'.format(command))
        session.execute(command)
    logger.info('successfully completed setting up "%s" keyspace', users_keyspace_name)