"""Synthetic data only: verify publication structure without network calls."""
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime,timezone
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_data

class PublicationTests(unittest.TestCase):
    def test_complete_schema_and_map_inventory(self):
        shape=(len(build_data.LAT),len(build_data.LON));array=np.ones(shape,dtype=np.float32)
        fields={key:array for key in build_data.PRODUCTS}
        def fake_load(path):return contextlib.nullcontext(fields)
        def fake_stats(members):return {key:array for key in ('mean','median','p10','p90')}
        def fake_render(*args):
            path=args[-1];path.parent.mkdir(parents=True,exist_ok=True);path.write_text('<svg/>')
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'build/data'
            with patch.object(build_data.np,'load',side_effect=fake_load),patch.object(build_data,'statistics',side_effect=fake_stats),patch.object(build_data,'render',side_effect=fake_render),contextlib.redirect_stdout(None):
                build_data.publish(datetime(2026,9,28,12,tzinfo=timezone.utc),Path('unused'),output)
            result=subprocess.run([sys.executable,str(Path(build_data.__file__).parent/'validate_data.py')],cwd=folder,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads((output/'departements/75.json').read_text(encoding='utf-8'))
            self.assertIsNone(data['forecast'][0][1][0][2])
            self.assertEqual(len(data['forecast']),65)
            self.assertIn('792',result.stdout)

if __name__=='__main__':unittest.main()
