#!/usr/bin/env python
'''
.. module:: files
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
import zipfile



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
