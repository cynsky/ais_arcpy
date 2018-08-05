'''
Script to process 2014 zone 10 data.
'''


# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import arcpy
import datetime
from glob import glob
from os.path import join
import pandas as pd
from mongoengine import *
import plinky
import logging

from nais import raw
import aws_mongo


# ------------------------------------------------------------------------------
# GLOBAL
# ------------------------------------------------------------------------------
months =  ["%02d" % i for i in range(1, 13)]
year = '2014'
zone = '10'

logger = logging.getLogger()


# ------------------------------------------------------------------------------
# PREPROCESS RAW
# ------------------------------------------------------------------------------
for month in months:
    raw_month = raw.Raw_Month('D:\\PhD\\ArcGIS Data', zone, year, month)
    raw_month.preprocess_month()

raw_mmsi = raw.Raw_MMSI('D:\\PhD\\CSV Data', zone, year)
raw_mmsi.preprocess_mmsi()
