import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from source import statistics,validate_message,url_for,STEPS,MAP_STEPS,IX,LON

class SourceTests(unittest.TestCase):
    def test_exact_ensemble_required(self):
        with self.assertRaises(ValueError):statistics({i:np.array([1.]) for i in range(30)})
        with self.assertRaises(ValueError):statistics({i:np.array([np.nan]) for i in range(31)})
    def test_ensemble_statistics(self):
        result=statistics({i:np.array([i],float) for i in range(31)})
        self.assertEqual(result['mean'][0],15);self.assertEqual(result['median'][0],15)
        self.assertEqual(result['p10'][0],3);self.assertEqual(result['p90'][0],27)
    def test_cumul_percentile_not_sum_of_percentiles(self):
        first={i:np.array([i],float) for i in range(31)}
        second={i:np.array([30-i],float) for i in range(31)}
        total={i:first[i]+second[i] for i in first}
        self.assertEqual(statistics(total)['p90'][0],30)
        self.assertNotEqual(statistics(first)['p90'][0]+statistics(second)['p90'][0],30)
    def test_wind_speed_not_norm_of_mean_vector(self):
        u=np.array([10]*15+[-10]*16);v=np.zeros(31)
        speeds={i:np.array([np.hypot(u[i],v[i])*3.6]) for i in range(31)}
        self.assertEqual(statistics(speeds)['mean'][0],36)
        self.assertLess(np.hypot(u.mean(),v.mean())*3.6,2)
    def test_step_coverage_and_no_zero_period(self):
        self.assertEqual(len(STEPS),65);self.assertEqual(STEPS[-1],384)
        self.assertEqual(len(MAP_STEPS),20);self.assertTrue(set(MAP_STEPS)<=set(STEPS))
    def test_longitude_wrap(self):
        self.assertEqual(IX[np.argmin(abs(LON))],0)
        self.assertEqual(IX[np.argmin(abs(LON+.25))],1439)
    def test_url_single_member_and_cycle(self):
        run=datetime(2026,9,28,6,tzinfo=timezone.utc)
        self.assertIn('/aigefs.20260928/06/mem030/model/atmos/grib2/aigefs.t06z.sfc.f384.grib2',url_for(run,30,384))
    def test_period_unit_member_and_run_validation(self):
        run=datetime(2026,9,28,6,tzinfo=timezone.utc)
        metadata={'Ni':1440,'Nj':721,'latitudeOfFirstGridPointInDegrees':90,'longitudeOfFirstGridPointInDegrees':0,'iDirectionIncrementInDegrees':.25,'jDirectionIncrementInDegrees':.25,'jScansPositively':0,'iScansNegatively':0,'jPointsAreConsecutive':0,'alternativeRowScanning':0,'numberOfMissing':0,'perturbationNumber':30,'numberOfForecastsInEnsemble':31,'dataDate':20260928,'dataTime':600,'endStep':384,'startStep':378,'stepType':'accum','units':'kg m**-2','typeOfLevel':'surface','level':0}
        validate_message(metadata.__getitem__,run,30,384,'tp')
        for key,value in [('startStep',0),('units','m'),('perturbationNumber',0),('dataTime',0),('numberOfMissing',1)]:
            wrong=dict(metadata);wrong[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_message(wrong.__getitem__,run,30,384,'tp')

if __name__=='__main__':unittest.main()
