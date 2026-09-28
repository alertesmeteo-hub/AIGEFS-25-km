import json
import sys
new=json.load(open(sys.argv[1],encoding='utf-8'))
old=json.load(open(sys.argv[2],encoding='utf-8'))
if new['run']<old['run']:
    raise SystemExit('Run plus ancien : publication existante conservée.')
