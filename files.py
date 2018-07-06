#!/usr/bin/env python
'''
.. module:: common
    :language: Python Version 2.7
    :platform: Windows 10
    :synopsis: commonly needed functions regarding files

.. moduleauthor:: Maura Rowell <mkrowell@uw.edu>
'''


# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import os
from os.path import abspath, basename, dirname, exists, join, splitext
import re
import zipfile


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
