# ais_arcpy
AIS data handling with Python

# Requires
arcpy

# Usage
The raw_month class downloads raw GDB data for a given year, month, and zone from MarineCadastre and processes it by:
- Splitting the year/month/zone file by the ship ID number
- Adding the latitude and longitude to the feature table
- Aggregating all files corresponding to a given ship ID number in a MMSI GDB

The raw_mmsi class downloads the US EEZ shapefile and selects only the data within the EEZ. The files in the MMSI GDB 
which do not contain any data in the US EEZ are deleted. The remaining shapefiles are written to csv.
```python
import arcpy
from os.path import join

from nais import raw


# ------------------------------------------------------------------------------
# GLOBAL
# ------------------------------------------------------------------------------
months =  ["%02d" % i for i in range(1, 13)]
year = '2014'
zone = '10'

# ------------------------------------------------------------------------------
# PREPROCESS RAW
# ------------------------------------------------------------------------------
for month in months:
    raw_month = raw.Raw_Month('C:\\PhD\\ArcGIS Data', zone, year, month)
    raw_month.preprocess()

raw_mmsi = raw.Raw_MMSI('C:\\PhD\\CSV Data', zone, year)
raw_mmsi.select_MMSI_in_EEZ()
```
