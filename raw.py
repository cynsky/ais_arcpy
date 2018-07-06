#!/usr/bin/env python
'''
.. module:: raw
    :language: Python Version 2.7.13
    :platform: Windows 10
    :synopsis: preprocess NAIS data from MarineCadastre

.. moduleauthor:: Maura Rowell <mkrowell@uw.edu>
'''


# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import arcpy
from arcpy import env
import csv
from datetime import datetime
import logging
import os
from os.path import exists, expanduser, join
import webbrowser

from . import util
from . import files


# ------------------------------------------------------------------------------
# RAW DATA OBJECT
# ------------------------------------------------------------------------------
class Raw_Month(object):

    '''
    The USCG stores historical AIS data gathered through NAIS and makes it 
    available by request and through MarineCadastre. This class downloads raw
    AIS data from MarineCadastre. The data is downloaded as a ArcGIS GDB for 
    each month. The main data file is the Broadcast shapefile which contains 
    the AIS dynamic data. This  file is split by the ship identification 
    number (MMSI). The latitude and longitude of each data point is added to 
    the feature table. Finally, the data for a given MMSI is aggregated in a 
    mmsi_gdb across months.
    '''

    def __init__(self, directory, zone, year, month):
        self.root = directory
        self.year = year
        self.month = month
        self.zone = zone
        self.parameters = (self.zone, self.year, self.month)

        # Arcpy environment
        self.workspace = join(self.root, self.year, self.month, 'Zone ' + self.zone)
        if not exists(self.workspace):
            os.makedirs(self.workspace)
        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = False

        # Geo-Databases
        self.gdb_raw = 'Zone%s_%s_%s.gdb' % self.parameters
        self.gdb_copy = 'Zone%s_%s_%s_MMSI.gdb' % self.parameters

        # Shapefile
        self.broadcast = 'Zone%s_%s_%s_Broadcast' % self.parameters

        # Logger
        self.logger = logging.getLogger(__name__)

    @property
    def url(self):
        '''
        Return the MarineCadastre URL corresponding to the year.
        '''
        param = (self.year, self.month, self.zone, self.year, self.month)
        if self.year == '2014':
            return 'https://coast.noaa.gov/htdata/CMSP/AISDataHandler/%s/%s/Zone%s_%s_%s.zip' % param
        if self.year == '2013':
            return 'https://coast.noaa.gov/htdata/CMSP/AISDataHandler/%s/%s/Zone%s_%s_%s.gdb.zip' % param

    @property
    def gdb_mmsi(self):
        '''
        Return path to MMSI gdb, create it if it doesn't exist.
        '''
        mmsi_folder = join(self.root, self.year, 'MMSI')
        if not exists(mmsi_folder):
            os.makedirs(mmsi_folder)

        name_mmsi = 'Zone%s_%s_MMSI.gdb' % (self.zone, self.year)
        gdb = join(mmsi_folder, name_mmsi)
        if not exists(gdb):
            arcpy.CreateFileGDB_management(mmsi_folder, name_mmsi)
        return gdb

    def download_raw_data(self):
        '''
        Download raw data from Marine Cadastre to local machine.
        '''
        if exists(join(self.workspace, self.gdb_raw)):
            self.logger.info('Data already downloaded for %s', self.month)
            return

        self.logger.info('Downloading data from %s:', self.url)
        zfile = util.download_url(self.url, self.workspace, '.zip')

        if not exists(join(self.workspace, self.gdb_raw)):
            self.logger.info('Extracting files from %s:', zfile)
            files.extract_zip(zfile, self.workspace)
            os.remove(zfile)

    def copy_raw_data(self):
        '''
        Make copy of original gdb in same directory.
        '''
        copy = join(self.workspace, self.gdb_copy)
        raw = join(self.workspace, self.gdb_raw)
        if not exists(copy):
            self.logger.info('Making copy of raw gdb: %s', self.gdb_copy)
            arcpy.Copy_management(raw, copy)
        else:
            self.logger.info('Copy of raw gdb already exits: %s', self.gdb_copy)

    def split_by_mmsi(self):
        '''
        Split the broadcast file by MMSI.

        After the broadcast file has been split by MMSI, it is deleted. This
        is used to prevent the splitting process from running more than once.
        '''
        input_file = join(self.gdb_copy, self.broadcast)
        if not arcpy.Exists(input_file):
            self.logger.info('%s already split by MMSI.', self.broadcast)
            return

        self.logger.info('Splitting %s by MMSI...', self.broadcast)
        arcpy.SplitByAttributes_analysis(input_file, self.gdb_copy, ['MMSI'])

        self.logger.info('Deleting input broadcast file %s', self.broadcast)
        arcpy.Delete_management(input_file)

    def status_check(self, list):
        '''
        Check that a list of status values contains a stop status 
        and a go status.
        '''
        stop = [1, 5, 6]
        go = [0, 2, 3, 4, 7, 8, 11, 12]
        has_stop = set(stop) & set(list)
        has_go = set(go) & set(list)
        if has_stop and has_go:
            return True
        return False

    def correct_status(self, fc):
        '''
        Check if feature class contains the correct status values.
        '''
        status = list()
        field = 'Status'
        with arcpy.da.SearchCursor(fc, [field]) as cursor:
            for row in cursor:
                status.append(row[0])
                if self.status_check(status):
                    return True
        return False

    def add_xy(self, fc):
        '''
        Add XY fields to feature class.
        '''
        fields = [f.name for f in arcpy.ListFields(fc)]
        if 'POINT_X' in fields and 'POINT_Y' in fields:
            self.logger.info('XY fields have already been added to %s...', fc)
            return

        self.logger.info('Adding XY fields to to %s...', fc)
        arcpy.AddXY_management(fc)

    def aggregate_month_mmsi(self, fc):
        '''
        Add the month shapefile to the MMSI geodatabase. If a file
        doesn't already exist in the MMSI gdb, copy over the month shapefile.
        If a file does exits, append the month shapefile to the existing
        MMSI file. Finally, delete the month shapefile (to prevent duplicate
        appending).
        '''
        name_fc = arcpy.Describe(fc).name
        mmsi_fc = join(self.gdb_mmsi, name_fc)

        if arcpy.Exists(mmsi_fc):
            self.logger.info('Appending %s...', name_fc)
            arcpy.Append_management(fc, mmsi_fc)
        else:
            self.logger.info('Copying %s...', name_fc)
            arcpy.Copy_management(fc, mmsi_fc)

        self.logger.info('Deleting month file for %s...', name_fc)
        arcpy.Delete_management(fc)

    def preprocess(self):
        '''
        Main method.
        '''
        print('Current arcpy workspace: %s' % arcpy.env.workspace)
        self.logger.info('Current arcpy workspace: %s', arcpy.env.workspace)
        self.download_raw_data()
        self.copy_raw_data()
        self.split_by_mmsi()

        self.logger.info('Getting list of feature classes in %s...', self.gdb_copy)
        arcpy.env.workspace = join(self.workspace, self.gdb_copy)
        featureClasses = arcpy.ListFeatureClasses()
        # Using 2013 data as "stop status" learning data
        for fc in featureClasses:
            if self.year == '2013' and not self.correct_status(fc):
                arcpy.Delete_management(fc)
                continue
            self.add_xy(fc)
            self.aggregate_month_mmsi(fc)


