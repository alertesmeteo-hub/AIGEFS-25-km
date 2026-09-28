import json
import math
from pathlib import Path
from source import STEPS,MAP_STEPS
root=Path('build/data');manifest=json.loads((root/'index.json').read_text(encoding='utf-8'))
assert manifest['members']==31 and manifest['commune_count']==34746
assert manifest['table_steps']==STEPS and manifest['steps']==MAP_STEPS
expected={f'{region}-{key}-{stat}-{step}.svg' for key,p in manifest['products'].items() for step in p['steps'] for region in ('france','europe') for stat in ('mean','median','p10','p90')}
assert {p.name for p in (root/'maps').glob('*.svg')}==expected
assert manifest['maps']==len(expected)==792
for path in (root/'maps').glob('*.svg'):assert '<image' not in path.read_text(encoding='utf-8')
departments=list((root/'departements').glob('*.json'));assert len(departments)==96
count=0
for path in departments:
    data=json.loads(path.read_text(encoding='utf-8'));count+=len(data['communes']);assert len(data['forecast'])==65
    for city in data['communes']:assert 0<=city[6]<len(data['points'])
    for step,(date,rows) in zip(STEPS,data['forecast']):
        assert len(rows)==len(data['points'])
        for row in rows:
            assert len(row)==33 and row[6] is None
            for key,p in manifest['products'].items():
                value=row[p['column']]
                if key=='rain6' and step==0:assert value is None
                else:assert isinstance(value,(float,int)) and math.isfinite(value)
            assert row[12]>=0
assert count==34746
print(f'Validation OK : {count} communes, 96 départements, 792 cartes SVG, 65 échéances tableaux.')
