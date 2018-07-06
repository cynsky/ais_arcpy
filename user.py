#!/usr/bin/env python
'''
.. module:: ais_arcpy.user
    :language: Python Version 2.7
    :platform: Windows 10
    :synopsis: commonly used user interface functions

.. moduleauthor:: Maura Rowell <mkrowell@uw.edu>
'''


# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import ctypes


# ------------------------------------------------------------------------------
# FUNCTIONS
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
