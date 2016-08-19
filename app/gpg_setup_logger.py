#!/usr/bin/python
# Copyright line goes here
"""
used to setup loggers
"""

__author__ = "GGibson"


import getpass
import logging
import logging.handlers
import os
import time


def setup_logger(log_dir, log_name_prefix, use_date_suffix=True, log_level=logging.DEBUG, format_string=None,
                 module=None, use_console_logger=True):
    """
    Create a logger, set up console and file handlers in the root logger
    NOTE: This should only be called once, from the script where __name__ == '__main__'
          other scripts should call logging.getLogger(__name__) as usual
    :param log_dir: Where to place the log. Will attempt to create if does not exist
    :param log_name_prefix: name to use as a prefix, i.e. <log_name>_<datetime>.log
    :param use_date_suffix: bool: use the date as a suffix to the log name
    :param log_level: initial logging level to set, default=INFO
    :param format_string: formatting string to use when logging to file. In None,
                          creates a standard format for scripts with classes
    :param module: Used to create the logger instance name, if None, then log_name_prefix is used
    :return: The constructed logger object
    """

    logger = logging.getLogger(module or log_name_prefix)
    logger.setLevel(log_level)

    # adjust the console logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            if use_console_logger:
                handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            else:
                root_logger.removeHandler(handler)
            break
    else:
        # Add a console handler
        if use_console_logger:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            root_logger.addHandler(handler)

    # create the file logger
    if not os.path.isdir(log_dir):
        try:
            os.makedirs(log_dir)
        except EnvironmentError as e:
            logger.exception('Failed to make log dir "{0}". Exception: {1}'.format(log_dir, str(e)))
            raise

    filename = os.path.join(log_dir, log_name_prefix)
    if use_date_suffix:
        filename += '_{0}'.format(time.strftime("%Y%m%d-%H%M%S"))
    filename += '.log'
    if use_console_logger:
        logger.debug("Setting up file logger with logfile '%s'", filename)
    mode = 'a'
    max_bytes = 1048576
    backup_count = 5
    fh = logging.handlers.RotatingFileHandler(filename, mode, max_bytes, backup_count)
    fh.setLevel(log_level)
    if not format_string:
        format_string = '%(asctime)s %(levelname)s %(name)s#%(funcName)s:%(lineno)d - %(message)s'
    file_formatter = logging.Formatter(format_string)
    fh.setFormatter(file_formatter)
    root_logger.addHandler(fh)
    return logger

def create_log_file_name(file_name):
    """
    Create a log name from a module's builtin __file__ attribute
    Useful if your script is called directly and the builtin __name__ == '__main__'
    :param file_name: Usually the built-in __file_attribute
    :return: The file_name stripped of path and (last) extension
    """
    return os.path.splitext(os.path.basename(file_name))[0]

def create_log_file_name_and_module(file_name, package, use_username=False):
    """
    Create a log file name from a module's builtin __file__ attribute and construct
    the module using the constructed file name and the module's builtin __package__ attribute
    :param file_name: Pass in the module's __file__ attribute
    :param package: Pass in the module's __package__ attribute. If None, the module will be returned
                    as None (a valid value for the setup_logger module parameter)
    :param use_username: bool: Whether to incorporate the user name into the log name, for use in contexts
                               where the log files need to be separated because of write permission conflicts
    :return: tuple(str, str): the constructed log file name and module name for use in calling setup_logger
                              They correspond to the log_name_prefix and module parameters in setup_logger
    """
    stripped_file = create_log_file_name(file_name)
    module = package
    if module:
        module = ".".join((module, stripped_file))
    if use_username:
        stripped_file += ".{0}".format(getpass.getuser())
    return stripped_file, module