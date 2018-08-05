#!/usr/bin/env python
'''
.. module:: ais_arcpy.util
    :language: Python Version 2.7
    :platform: Windows 10
    :synopsis: utility functions for package

.. moduleauthor:: Maura Rowell <mkrowell@uw.edu>
'''



# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import certifi
import ctypes
import datetime
import logging
import os
from os.path import abspath, exists, join
import pycurl
import re
import zipfile


# ------------------------------------------------------------------------------
# PARAMETERS
# ------------------------------------------------------------------------------
logger = logging.getLogger(__name__)

now = datetime.datetime.now()
sf = '%(asctime)s - %(levelname)s - line %(lineno)d - %(funcName)s - %(message)s'
stdFormatter = logging.Formatter(sf, datefmt = '%Y-%m-%d %H.%M.%S')


# ------------------------------------------------------------------------------
# EXCEPTIONS
# ------------------------------------------------------------------------------
class fileNotFound(Exception):
    def __init__(self, directory, filename, msg = None):
        if msg is None:
            msg = ('The file {0} was not found in the directory: {1}').format(
                  filename, directory)
        super(fileNotFound, self).__init__(msg)
        self.directory = directory
        self.filename = filename


# ------------------------------------------------------------------------------
# WEB
# ------------------------------------------------------------------------------
def download_url(url, destination, fileExtension = '.xls'):
    '''
    Write url to temp file.
    :param url: URL to download data from
    :param destination: Path to download data to
    :param fileExtension: extension to use for temp file

    :type url: string
    :type destination: string
    :type fileExtension: string
    :return: Path to temp file containing URL data
    :rtype: string
    '''
    tempFile = join(destination, 'temp_data' + fileExtension)
    with open(tempFile, 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(pycurl.CAINFO, certifi.where())
        c.setopt(c.WRITEDATA, f)
        c.perform()
        c.close()
    logger.info('Downloaded file to %s.', tempFile)
    return tempFile


# ------------------------------------------------------------------------------
# USER
# ------------------------------------------------------------------------------
def message_box_OK_Cancel(title, msg):
    '''
    Open a message box with OK and Cancel button options.

    :param title: Title of the message box
    :param msg: Message to show in message box

    :type title: string
    :type msg: string

    :return: Message box
    :rtype: cytpes.windll.user32.MessageBox
    '''
    return ctypes.windll.user32.MessageBoxW(0, msg, title, 1)


# ------------------------------------------------------------------------------
# LOG
# ------------------------------------------------------------------------------
def add_handler(logger, level, formatter, filepath):
    '''
    Configure logging handler with a level, formatter, and output filename.

    :param logger: Logger to add a file handler to
    :param level: Handler level
    :param formatter: Handler output format
    :param filepath: Handler output filepath

    :type logger: Logging logger
    :type level: Logging level
    :type formatter: format string
    :type filepath: string
    '''
    handler = logging.FileHandler(filepath, 'w')
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def initialize_logger(directory, level = logging.DEBUG):
    '''
    Creates a logger with one file handler. The file is saved to the directory
    provided. The standard formatter is used and the default level is DEBUG.

    :param directory: Directory to save log file to
    :param level: Logging level, default is DEBUG

    :type directory: string
    :type level: Logging level

    :return: Log object to use for logging within script
    :rtype: Logging logger
    '''
    if not exists(directory):
        os.mkdir(directory)

    logger = logging.getLogger()
    logger.setLevel(level)

    name = 'log '+ now.strftime('%Y-%m-%d %H.%M.%S') + '.log'
    filepath = join(directory, name)
    add_handler(logger, level, stdFormatter, filepath)

    logger.info('********** Script began at %s **********', str(now))
    return logger

def close_logger(logger):
    '''
    Removes the handlers from and closes the logger.

    :param logger: Logger to close
    :type logger: Logging logger
    '''
    logger.info('********** Script ended at %s **********', str(now))
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)


# ------------------------------------------------------------------------------
# FILE SYSTEM
# ------------------------------------------------------------------------------
def create_folder(parent, name):
    '''
    Create a folder with given name as a subdirectory of parent, if the
    folder does not already exist, and return path to the folder.

    :param parent: Directory in which the folder will be created
    :param name: Name of the folder to be created

    :type parent: string
    :type name: string

    :return: Path to folder
    :rtype: string
    '''
    folder = abspath(join(parent, name))
    if not exists(folder):
        try:
            os.makedirs(folder)
        except IOError as err:
            folderExistsCode = 17
            if err.errno != folderExistsCode:
                raise err
    return folder

def find_file(directory, filename):
    '''
    Search for a filename in the directory and return the full path. The
    extension does not need to be included, but the first filepath that
    matches will be returned.

    :param directory: Directory within which to search for file
    :param filename: Name of file, with or without extension, to search for

    :type directory: string
    :type filename: string

    :return: Path to file
    :rtype: string
    :raises fileNotFound: Filename cannot be located within the directory
    '''
    rex = re.compile(filename.lower())
    for root, dirs, files in os.walk(directory):
        for f in files:
            result = rex.search(f.lower())
            if result:
                return join(root, f)
    raise fileNotFound(directory, filename)


# ------------------------------------------------------------------------------
# ZIP FILES
# ------------------------------------------------------------------------------
def extract_zip(filepath, destination):
    '''
    Extract zip file to the destination and return list of filenames contained
    within the archive.

    :param filepath: Filepath to the zip file to be unzipped
    :param destination: Location for the archive files to be extracted to

    :type filepath: string
    :type destination: string

    :return: List of filenames that have been extracted to the destination
    :rtype: list of strings
    '''
    zfile = zipfile.ZipFile(filepath, 'r')
    zfile.printdir()
    zfile.extractall(destination)
    zfile.close()
    return zfile.namelist()

def extract_file(filepath, destination):
    '''
    Return the path to the first file extracted from a zip file.
    '''
    zf = extract_zip(filepath, destination)
    if len(zf) == 1:
        name = zf[0]
        return join(destination, name)
    raise UserWarning('There are multiple files in the zip file.')
