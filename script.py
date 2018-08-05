'''
Script to process 2014 zone 10 data.
'''


# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import arcpy
import logging

from ais_arcpy import raw


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
