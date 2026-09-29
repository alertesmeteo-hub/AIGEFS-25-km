"""Full 31-member, 6-hourly ingestion; compact France/Europe map publication."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import timedelta,datetime,timezone
import json
from pathlib import Path
import requests
import numpy as np
from source import latest_run,url_for,download,decode,statistics,STEPS,MAP_STEPS,MEMBERS,LON,LAT,IX,IY
from render_maps import PRODUCTS,REGIONS,render

def extract_member(run,member,cache):
    session=requests.Session();total=np.zeros((len(LAT),len(LON)),np.float32)
    for step in STEPS:
        values=decode(download(session,url_for(run,member,step)),run,member,step)
        if step:total=total+values['rain6']
        values['precipitation']=total
        np.savez_compressed(cache/f'{member:03d}-{step:03d}.npz',**values)
        if step%96==0:print(f'Membre {member:03d}: H+{step} validé',flush=True)
    return member

def publish(run,cache,output):
    output.mkdir(parents=True,exist_ok=True)
    table_stats={};map_count=0
    products={key:dict(spec) for key,spec in PRODUCTS.items()}
    for key,spec in products.items():spec['steps']=[step for step in MAP_STEPS if key!='rain6' or step>0]
    for step in STEPS:
        members={key:{} for key in PRODUCTS if key!='rain6' or step>0}
        for member in range(MEMBERS):
            with np.load(cache/f'{member:03d}-{step:03d}.npz') as fields:
                for key in members:members[key][member]=fields[key]
        table_stats[step]={stat:{} for stat in ('mean','median','p10','p90')}
        for key,arrays in members.items():
            stats=statistics(arrays)
            for stat,values in stats.items():table_stats[step][stat][key]=values
            if step in MAP_STEPS:
                for stat,values in stats.items():
                    for region in REGIONS:
                        render(LON,LAT,values,key,stat,region,run,step,output/'maps'/f'{region}-{key}-{stat}-{step}.svg');map_count+=1
        print(f'H+{step}: statistiques des 31 membres et cartes validées',flush=True)
    raw=json.loads(Path('config/communes-france.json').read_text(encoding='utf-8'))['communes'];departments={}
    for city in raw:departments.setdefault(city[2],[]).append(city)
    if len(raw)!=34746 or len(departments)!=96:raise ValueError('Catalogue national incomplet')
    schema=json.loads(Path('config/reference-schema.json').read_text(encoding='utf-8'))
    (output/'departements').mkdir(exist_ok=True);cities=[]
    for code,communes in departments.items():
        points=[];city_rows=[];lookup={}
        for c in communes:
            iy=int(np.argmin(abs(LAT-c[5])));ix=int(np.argmin(abs(LON-c[6])))
            if (iy,ix) not in lookup:
                lookup[iy,ix]=len(points);points.append([int(IY[iy]*1440+IX[ix]),float(LAT[iy]),float(LON[ix]),None])
            city_rows.append([c[0],c[1],c[3],c[4],c[5],c[6],lookup[iy,ix]]);cities.append([c[0],c[1],code])
        forecasts={}
        for stat in ('mean','median','p10','p90'):
            forecast=[]
            for step in STEPS:
                rows=[]
                for iy,ix in lookup:
                    row=[None]*33
                    for key,values in table_stats[step][stat].items():row[PRODUCTS[key]['column']]=round(float(values[iy,ix]),2)
                    rows.append(row)
                forecast.append([(run+timedelta(hours=step)).isoformat(),rows])
            forecasts[stat]=forecast
        payload={'schema_version':4,'columns':schema,'department':code,'members':31,'statistic':'mean','points':points,'communes':city_rows,'forecast':forecasts['mean'],'forecast_statistics':{key:value for key,value in forecasts.items() if key!='mean'}}
        (output/'departements'/f'{code}.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    (output/'communes.json').write_text(json.dumps(cities,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    manifest={'status':'ok','version':'1.1.0','model':'AIGEFS','members':31,'run':run.isoformat(),'generated_at':datetime.now(timezone.utc).isoformat(),'steps':MAP_STEPS,'table_steps':STEPS,'products':products,'maps':map_count,'commune_count':len(cities),'source':'NOAA/NCEP NOMADS','limitations':'Vent à 10 m, pas de rafales. Précipitations sur 6 h et cumul depuis le run en équivalent eau. Pas de précipitations 6 h à H+0. Statistiques des 31 membres ; pas de prévisions horaires interpolées.'}
    (output/'index.json').write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run');args=parser.parse_args()
    run=datetime.strptime(args.run,'%Y%m%d%H').replace(tzinfo=timezone.utc) if args.run else latest_run()
    print('Run sélectionné : '+run.isoformat(),flush=True)
    cache=Path('build/cache')/run.strftime('%Y%m%d%H');cache.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks=[pool.submit(extract_member,run,member,cache) for member in range(MEMBERS)]
        for task in as_completed(tasks):print(f'Membre {task.result():03d} complet',flush=True)
    publish(run,cache,Path('build/data'))

if __name__=='__main__':main()

