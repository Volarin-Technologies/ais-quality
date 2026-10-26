import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from ais_quality import analyze, export_reports, render

class ReleaseTests(unittest.TestCase):
    def make(self, directory, body):
        p=Path(directory)/'input.csv'
        p.write_text('mmsi,timestamp,lat,lon,source\n'+body)
        return p

    def test_conflict_all_rows_flagged_original_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(d,'999000001,2026-01-01T00:00:00Z,0,0,A\n999000001,2026-01-01T00:00:00Z,0,1,B\n999000001,2026-01-01T00:05:00Z,0,2,C\n')
            r=analyze(p)
            self.assertEqual(r['counts']['position_conflict'],2)
            self.assertEqual(r['movement_segments'],[])
            self.assertEqual(r['flagged_records'][0]['original']['source'],'A')
            self.assertEqual(r['issues'][0]['severity'],'warning')

    def test_movement_threshold_and_gap_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(d,'999000001,2026-01-01T00:00:00Z,0,0,A\n999000001,2026-01-01T00:05:00Z,0,1,B\n')
            r=analyze(p)
            self.assertEqual(r['counts'],{'speed_exceeded':1,'position_jump':1})
            self.assertEqual(r['flagged_records'][0]['original']['source'],'B')
            self.assertEqual(analyze(p,max_speed_knots=1000,max_jump_nm=100)['flagged_rows'],0)
            self.assertEqual(analyze(p,gap_minutes=1)['flagged_rows'],0)

    def test_explicit_utc_and_noaa_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'noaa.csv';p.write_text('mmsi,base_date_time,latitude,longitude\n338075892,2024-01-01 00:00:03,43.65322,-70.25298\n')
            self.assertIn('invalid_timestamp',analyze(p)['counts'])
            self.assertEqual(analyze(p,assume_utc=True)['flagged_rows'],0)

    def test_limits_and_invalid_configuration(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(d,'999000001,2026-01-01T00:00:00Z,0,0,A\n999000001,2026-01-01T00:05:00Z,0,0,B\n')
            for kw in [dict(max_rows=1),dict(max_bytes=1),dict(max_speed_knots=0),dict(max_jump_nm=float('nan')),dict(language='de')]:
                with self.assertRaises(ValueError):analyze(p,**kw)

    def test_language_and_csv_guidance(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(d,'invalid,2026-01-01T00:00:00Z,0,0,A\n')
            en=analyze(p);pt=analyze(p,language='pt')
            self.assertIn('Invalid MMSI structure',render(en))
            self.assertIn('Estrutura de MMSI',render(pt))
            export_reports(pt,Path(d)/'reports')
            with (Path(d)/'reports/issues.csv').open() as f:
                row=next(csv.DictReader(f))
            self.assertTrue(row['recommendation'])

    def test_cli_failures_do_not_write_reports(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.make(d,'bad,bad,bad,bad,A\n')
            out=Path(d)/'reports'
            run=subprocess.run([sys.executable,'ais_quality.py',str(p),'--max-rows','0','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(run.returncode,2)
            self.assertFalse(out.exists())
            self.assertNotIn('Traceback',run.stderr)

    def test_real_sample_integrity(self):
        import hashlib
        provenance=json.loads(Path('examples/real-noaa.provenance.json').read_text())
        self.assertEqual(hashlib.sha256(Path('examples/real-noaa.csv').read_bytes()).hexdigest(),provenance['sha256'])
        r=analyze('examples/real-noaa.csv',assume_utc=True)
        self.assertEqual(r['total_rows'],5000)
        self.assertNotIn('invalid_timestamp',r['counts'])
