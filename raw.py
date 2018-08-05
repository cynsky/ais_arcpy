#!/usr/bin/env python
'''
.. module:: ais_arcpy.raw
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


# ------------------------------------------------------------------------------
# RAW DATA OBJECT
# ------------------------------------------------------------------------------
class Raw_Month(object):

    '''
    Process raw NAIS data from MarineCadastre. The data is downloaded in
    ArcGIS format for each month.

    The data is split by zone, year, and month. This class downloads the data
    from MarineCadastre for the given zone, year, and month. The main data
    file is the Broadcast shapefile which contains the AIS dynamic data. This
    file is split by the ship identification number (MMSI). The latitude and
    longitude of each data point is added to the feature table. Finally, the
    data for a given MMSI is aggregated in a mmsi_gdb across months.
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

    def preprocess_month(self):
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
        for fc in featureClasses:
            self.add_xy(fc)
            self.aggregate_month_mmsi(fc)

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


class Raw_MMSI(object):

    '''
    Process monthly MMSI files.
    '''

    def __init__(self, directory, zone, year):
        '''
        Create instance of raw data for a given year, month, and zone.
        '''
        self.root = directory
        self.year = year
        self.zone = zone

        # Arcpy parameters
        self.workspace = join(self.root, self.year, 'MMSI')
        arcpy.env.workspace = self.workspace
        arcpy.env.overwriteOutput = False

        # MMSI gdb
        self.gdb_mmsi = 'Zone%s_%s_MMSI.gdb' % (self.zone, self.year)

        # Fields
        self.fields = [
            'SOG',
            'COG',
            'Heading',
            'ROT',
            'BaseDateTime',
            'Status',
            'VoyageID',
            'MMSI',
            'ReceiverType',
            'POINT_X',
            'POINT_Y']

        # EEZ shapefile
        self.eez_world = join(self.root, 'World EEZ', 'eez_v10.shp')
        self.eez = join(self.root, 'World EEZ', 'eez_us.shp')

        # Logger
        self.logger = logging.getLogger()


    def preprocess_mmsi(self):
        '''
        Select only EEZ points and write to csv.
        '''
        self.download_eez()
        self.make_eez_us()

        arcpy.env.workspace = join(self.workspace, self.gdb_mmsi)
        featureClasses = arcpy.ListFeatureClasses()
        for fc in featureClasses:
            name = arcpy.Describe(fc).name
            if '_eez' in name:
                continue
            self.select_eez(fc)
        featureClasses = arcpy.ListFeatureClasses()
        for fc in featureClasses:
            self.to_csv(fc)

    def download_eez(self):
        '''
        Download World EEZ and extract US EEZ.
        '''
        folder = files.create_folder(self.root, 'World EEZ')
        url = 'http://www.marineregions.org/download_file.php?name=World_EEZ_v10_20180221.zip'
        if not exists(join(folder, self.eez_world)):
            text = u'Please download the World EEZ file'
            result = user.message_box_OK_Cancel(text, text)
            if result == 2:
                return
            if result == 1:
                webbrowser.open(url)
                title = u'Extract US EEZ'
                msg = u'Select \'OK\' to extract files to %s.' % folder
                result1 = user.message_box_OK_Cancel(title, msg)
                if result1 == 2:
                    return

        downloads = join(expanduser("~"), 'Downloads')
        tempfile = files.find_file(downloads, 'World_EEZ')
        self.logger.info('Extracting files from %s:', tempfile)
        files.extract_zip(tempfile, folder)
        os.remove(tempfile)

    def make_eez_us(self):
        '''
        Select the US EEZ from the World EEZself.
        '''
        arcpy.env.workspace = join(self.root, 'World EEZ')
        if arcpy.Exists(self.eez):
            return

        name_world = arcpy.Describe(self.eez_world).name
        name_lyr = name_world + '_lyr'
        name_us = 'eez_us'

        self.logger.info('Creating an in_memory layer for %s...', name_world)
        arcpy.MakeFeatureLayer_management(name_world, name_lyr)

        self.logger.info('Selecting by geo name within EEZ...')
        arcpy.SelectLayerByAttribute_management(
            name_lyr,
            "NEW_SELECTION",
            "GeoName = 'United States Exclusive Economic Zone'")

        self.logger.info('Saving the in_memory layer to disk.')
        arcpy.CopyFeatures_management(name_lyr, name_us)

    def select_eez(self, fc):
        '''
        Select only points in EEZ.
        '''
        name_mmsi = arcpy.Describe(fc).name
        name_lyr = name_mmsi + "_lyr"
        name_eez = name_mmsi + "_eez"

        if arcpy.Exists(name_eez):
            return

        # Make in_memory temporary layer
        self.logger.info('Creating an in_memory layer for %s...', name_lyr)
        arcpy.MakeFeatureLayer_management(name_mmsi, name_lyr)

        # Select features that are inside US EEZ
        self.logger.info('Selecting by location within EEZ...')
        arcpy.SelectLayerByLocation_management(name_lyr, 'within', self.eez)

        # If there are more than zero features, save the layer
        if arcpy.GetCount_management(name_lyr) > 2:
            self.logger.info('Saving the in_memory layer to disk.')
            arcpy.CopyFeatures_management(name_lyr, name_eez)

        # Delete in_memory temporary file
        self.logger.info('Deleting in_memory layer %s', name_lyr)
        arcpy.Delete_management(name_lyr)
        # Delete original file
        self.logger.info('Deleting original shapefile %s', name_mmsi)
        arcpy.Delete_management(name_mmsi)

    # def add_time_index(self, fc):
    #     field = 'BaseDateTime'
    #     arcpy.AddIndex_management(fc, [field], 'DateTimeIndex', 'UNIQUE', 'ASCENDING')

    def to_csv(self, fc):
        '''
        Write shapefile to csv.
        '''
        path = join(self.root, self.year)
        name_mmsi = arcpy.Describe(fc).name
        name_csv = name_mmsi + '.csv'
        file_out = join(path, name_csv)
        if not exists(file_out):
            with open(file_out, 'wb') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(self.fields)
                with arcpy.da.SearchCursor(fc, self.fields) as cursor:
                    for row in cursor:
                        writer.writerow(row)
