#!/usr/bin/env python
'''
.. module:: ais_arcpy.util
    :language: Python Version 2.7
    :platform: Windows 10
    :synopsis: commonly needed utility functions

.. moduleauthor:: Maura Rowell <mkrowell@uw.edu>
'''



# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import certifi
import logging
from os.path import join
import pycurl


# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
logger = logging.getLogger(__name__)


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
