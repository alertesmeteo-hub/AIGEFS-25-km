import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_data
from source import LON,LAT
from render_maps import render

class PipelineTests(unittest.TestCase):
    def test_all_six_hour_intervals_are_summed_before_statistics(self):
        shape=(len(LAT),len(LON));saved={};run=datetime(2026,9,28,6,tzinfo=timezone.utc)
        def decoded(data,run,member,step):
            result={'temperature':np.ones(shape),'vent':np.ones(shape),'pressure':np.ones(shape)*1010}
            if step:result['rain6']=np.ones(shape)*(2 if step==6 else 3)
            return result
        def save(path,**fields):saved[path.name]={key:value.copy() for key,value in fields.items()}
        with patch.object(build_data,'STEPS',[0,6,12]),patch.object(build_data,'download',return_value=b'') as download,patch.object(build_data,'decode',side_effect=decoded),patch.object(build_data.np,'savez_compressed',side_effect=save):
            build_data.extract_member(run,0,Path('unused'))
        self.assertEqual(download.call_count,3)
        self.assertTrue(np.all(saved['000-012.npz']['precipitation']==5))
        self.assertTrue(np.all(saved['000-006.npz']['precipitation']==2))
        self.assertNotIn('rain6',saved['000-000.npz'])
    def test_precipitation_map_is_vector_and_period_labelled(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'test.svg'
            render(LON,LAT,np.zeros((len(LAT),len(LON))),'rain6','mean','france',datetime(2026,9,28,6,tzinfo=timezone.utc),12,output)
            text=output.read_text(encoding='utf-8')
            self.assertNotIn('<image',text)
            self.assertIn('31 membres',text)
            self.assertIn('28/09 12 UTC',text)
            self.assertIn('28/09 18 UTC',text)

if __name__=='__main__':unittest.main()
