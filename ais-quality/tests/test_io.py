import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ais_quality import analyze, export_reports

class OutputTests(unittest.TestCase):
    def test_staging_preserves_existing_files_on_render_error(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'report.json';p.write_text('old')
            with patch('ais_quality.render',side_effect=ValueError('render failure')):
                with self.assertRaises(ValueError):export_reports(analyze('examples/sample.csv'),d)
            self.assertEqual(p.read_text(),'old')
            self.assertEqual(list(Path(d).iterdir()),[p])

    def test_cli_protects_input_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'issues.csv';data='mmsi,timestamp,lat,lon\n';p.write_text(data)
            r=subprocess.run([sys.executable,'ais_quality.py',str(p),'--output',d],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
            self.assertEqual(p.read_text(),data)
