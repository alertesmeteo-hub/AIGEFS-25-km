"""Read-only diagnostic of a downloaded NOAA GRIB."""
import sys
import eccodes as e
KEYS=['shortName','units','typeOfLevel','level','Ni','Nj','latitudeOfFirstGridPointInDegrees','longitudeOfFirstGridPointInDegrees','iDirectionIncrementInDegrees','jScansPositively','jPointsAreConsecutive','perturbationNumber','numberOfForecastsInEnsemble','startStep','endStep','stepType','dataDate','dataTime','minimum']
with open(sys.argv[1],'rb') as stream:
    while (handle:=e.codes_grib_new_from_file(stream)) is not None:
        try:
            print({key:e.codes_get(handle,key) for key in KEYS})
        finally:e.codes_release(handle)
