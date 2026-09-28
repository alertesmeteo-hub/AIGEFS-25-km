"""Manual integration test of real downloaded NOAA files; not part of CI."""
from datetime import datetime,timezone
from pathlib import Path
from source import decode
run=datetime(2026,9,28,6,tzinfo=timezone.utc)
for file,member,step in [('sample006.grib2',0,6),('sample000-m30.grib2',30,0)]:
    result=decode((Path('build')/file).read_bytes(),run,member,step)
    print(file,{key:(round(float(value.min()),2),round(float(value.max()),2)) for key,value in result.items()})
