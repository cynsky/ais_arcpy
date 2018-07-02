# ais_arcpy
AIS data handling with Python

# Requires
arcpy

# Usage
The class downloads raw GDB data for a given year, month, and zone from MarineCadastre and processes it by:
- Splitting the year/month/zone file by the ship ID number
- Adding the latitude and longitude to the feature table
- Aggregating all files corresponding to a given ship ID number in a MMSI GDB

```python
import arcpy
from os.path import join

from .ais_arcpy import raw


# ------------------------------------------------------------------------------
# GLOBAL
# ------------------------------------------------------------------------------
root = 'C:\\Users\\User\\Documents\\ArcGIS Data'

year = '2014'
months =  ["%02d" % i for i in range(1, 13)]
zone = '10'


# ------------------------------------------------------------------------------
# PREPROCESS RAW
# ------------------------------------------------------------------------------
for month in months:
    raw_month = raw.Raw_Month(root, zone, year, month)
    raw_month.preprocess()
```
