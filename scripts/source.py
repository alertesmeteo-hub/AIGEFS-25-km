"""Strict ingestion of operational NOAA AIGEFS surface ensemble files."""
from datetime import datetime,timezone
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import io
import re
import time
import threading
import requests
import numpy as np
import eccodes as e

BASE='https://nomads.ncep.noaa.gov/pub/data/nccf/com/aigefs/prod/'
MEMBERS=31
STEPS=list(range(0,385,6))
MAP_STEPS=[0,6,12,18]+list(range(24,385,24))
LON=np.arange(-26,46.01,.25);LAT=np.arange(29,73.01,.25)
IX=np.rint((LON%360)/.25).astype(int);IY=np.rint((90-LAT)/.25).astype(int)
_request_lock=threading.Lock()
_last_request=0.0

def pace():
    """Global cap below 60 requests/minute, shared by all worker threads."""
    global _last_request
    with _request_lock:
        remaining=1.5-(time.monotonic()-_last_request)
        if remaining>0:time.sleep(remaining)
        _last_request=time.monotonic()

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.links.extend(v for k,v in attrs if k=='href')

def listing(session,url):
    pace()
    response=session.get(url,timeout=(15,60));response.raise_for_status()
    parser=Links();parser.feed(response.text);return parser.links

def url_for(run,member,step):
    return f'{BASE}aigefs.{run:%Y%m%d}/{run:%H}/mem{member:03d}/model/atmos/grib2/aigefs.t{run:%H}z.sfc.f{step:03d}.grib2'

def latest_run():
    session=requests.Session()
    days=sorted([s for s in listing(session,BASE) if re.fullmatch(r'aigefs\.\d{8}/',s)],reverse=True)
    checked=0
    for day in days[:2]:
        cycles=sorted([s for s in listing(session,BASE+day) if re.fullmatch(r'(00|06|12|18)/',s)],reverse=True)
        for cycle in cycles:
            run=datetime.strptime(day[7:15]+cycle[:2],'%Y%m%d%H').replace(tzinfo=timezone.utc)
            # Last lead for every member must already exist; do not mix cycles.
            def probe(member):
                pace()
                with requests.head(url_for(run,member,384),timeout=(15,45)) as response:return response.status_code
            with ThreadPoolExecutor(max_workers=3) as pool:
                statuses=list(pool.map(probe,range(MEMBERS)))
            if all(status==200 for status in statuses):return run
            checked+=1
            if checked>=4:break
    raise ValueError('Aucun run complet AIGEFS à 31 membres et H+384 disponible')

def download(session,url):
    for attempt in range(3):
        try:
            pace()
            with session.get(url,stream=True,timeout=(20,90)) as response:
                response.raise_for_status();chunks=[];size=0
                for chunk in response.iter_content(1024*1024):
                    size+=len(chunk)
                    if size>20_000_000:raise ValueError('Fichier surface anormalement volumineux')
                    chunks.append(chunk)
            data=b''.join(chunks)
            if not data.startswith(b'GRIB') or not data.endswith(b'7777'):
                raise requests.RequestException(f'Réponse non GRIB ou tronquée : {url}, {len(data)} octets')
            return data
        except requests.RequestException as error:
            if attempt==2:raise
            print(f'Téléchargement à reprendre ({error}); attente {60*(attempt+1)} s.',flush=True)
            time.sleep(60*(attempt+1))

def validate_message(get,run,member,step,name):
    expected={'Ni':1440,'Nj':721,'latitudeOfFirstGridPointInDegrees':90,
        'longitudeOfFirstGridPointInDegrees':0,'iDirectionIncrementInDegrees':.25,
        'jDirectionIncrementInDegrees':.25,'jScansPositively':0,'iScansNegatively':0,
        'jPointsAreConsecutive':0,'alternativeRowScanning':0,'numberOfMissing':0,
        'perturbationNumber':member,'numberOfForecastsInEnsemble':31,
        'dataDate':int(run.strftime('%Y%m%d')),'dataTime':run.hour*100,
        'endStep':step,'startStep':step-6 if name=='tp' else step,
        'stepType':'accum' if name=='tp' else 'instant'}
    units={'10u':'m s**-1','10v':'m s**-1','2t':'K','prmsl':'Pa','tp':'kg m**-2'}
    levels={'10u':('heightAboveGround',10),'10v':('heightAboveGround',10),'2t':('heightAboveGround',2),'prmsl':('meanSea',0),'tp':('surface',0)}
    expected.update(units=units[name],typeOfLevel=levels[name][0],level=levels[name][1])
    for key,value in expected.items():
        if get(key)!=value:raise ValueError(f'{name} membre {member} H+{step}: {key} invalide ({get(key)!r})')

def decode(data,run,member,step):
    values={};offset=0
    while offset<len(data):
        if data[offset:offset+4]!=b'GRIB':raise ValueError('Entête GRIB invalide')
        size=int.from_bytes(data[offset+8:offset+16],'big')
        if size<20 or offset+size>len(data):raise ValueError('Longueur GRIB invalide')
        handle=e.codes_new_from_message(data[offset:offset+size]);offset+=size
        try:
            name=e.codes_get(handle,'shortName')
            if name not in ('10u','10v','2t','prmsl','tp') or name in values:raise ValueError('Champ inattendu ou dupliqué')
            validate_message(lambda key:e.codes_get(handle,key),run,member,step,name)
            array=e.codes_get_values(handle).reshape(721,1440)[np.ix_(IY,IX)].astype(np.float32)
            if not np.isfinite(array).all():raise ValueError('Valeurs manquantes')
            values[name]=array
        finally:e.codes_release(handle)
    required={'10u','10v','2t','prmsl'}|({'tp'} if step else set())
    if set(values)!=required:raise ValueError('Champs surface incomplets')
    result={'temperature':values['2t']-273.15,'vent':np.hypot(values['10u'],values['10v'])*3.6,'pressure':values['prmsl']/100}
    if step:
        if values['tp'].min()<0:raise ValueError('Précipitations négatives')
        result['rain6']=values['tp']
    return result

def statistics(members):
    if set(members)!=set(range(MEMBERS)):raise ValueError('Les 31 membres sont obligatoires')
    values=np.stack([members[i] for i in range(MEMBERS)])
    if not np.isfinite(values).all():raise ValueError('Valeurs non finies')
    return {'mean':values.mean(axis=0),'median':np.median(values,axis=0),'p10':np.quantile(values,.1,axis=0),'p90':np.quantile(values,.9,axis=0)}
