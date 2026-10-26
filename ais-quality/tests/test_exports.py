import csv
import json
import tempfile
import unittest
from pathlib import Path
from ais_quality import analyze, export_reports, parse_columns, resolve_columns

class ExportTests(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(resolve_columns(['MMSI', 'BaseDateTime', 'LAT', 'LON']),
                         {'mmsi': 'MMSI', 'timestamp': 'BaseDateTime', 'lat': 'LAT', 'lon': 'LON'})

    def test_ambiguous_and_explicit_columns(self):
        headers = ['mmsi', 'timestamp', 'lat', 'latitude', 'lon']
        with self.assertRaises(ValueError):
            resolve_columns(headers)
        self.assertEqual(resolve_columns(headers, {'lat': 'latitude'})['lat'], 'latitude')
        for mapping in ({'lat': 'missing'}, {'unknown': 'lat'}, {'lat': 'mmsi'}):
            with self.assertRaises(ValueError):
                resolve_columns(headers, mapping)

    def test_mapping_parser(self):
        self.assertEqual(parse_columns(['lat=Y', 'lon=X']), {'lat': 'Y', 'lon': 'X'})
        for items in (['bad'], ['lat='], ['lat=X', 'lat=Y'], ['speed=X']):
            with self.assertRaises(ValueError):
                parse_columns(items)

    def test_alias_end_to_end_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            path.write_text('MMSI,BaseDateTime,LAT,LON\n999000001,2026-01-01T12:00:00Z,0,0\n999000001,2026-01-01T13:00:00Z,91,0\ninvalid,bad,0,0\n')
            report = analyze(path)
            self.assertEqual(report['vessels'][0]['total_rows'], 2)
            self.assertEqual(report['vessels'][0]['flagged_rows'], 1)
            self.assertEqual(report['vessels'][0]['gap_count'], 1)
            self.assertEqual(len(report['flagged_records']), 2)
            export_reports(report, Path(directory) / 'reports')
            saved = json.loads((Path(directory) / 'reports/report.json').read_text())
            self.assertEqual(saved, report)
            with (Path(directory) / 'reports/flagged_records.csv').open() as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 2)
            self.assertEqual(json.loads(rows[0]['original_record_json'])['LAT'], '91')

    def test_formula_export_and_no_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            path.write_text('mmsi,timestamp,lat,lon\n=1+1,bad,-23,-46\n')
            report = analyze(path)
            export_reports(report, directory)
            with (Path(directory) / 'flagged_records.csv').open() as source:
                row = next(csv.DictReader(source))
            self.assertEqual(row['mmsi'], "'=1+1")
            self.assertEqual(report['flagged_records'][0]['values']['mmsi'], '=1+1')
            path.write_text('mmsi,timestamp,lat,lon\n')
            export_reports(analyze(path), directory)
            with (Path(directory) / 'flagged_records.csv').open() as source:
                self.assertEqual(list(csv.DictReader(source)), [])

    def test_extra_cells_are_not_false_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            path.write_text('mmsi,timestamp,lat,lon\n999000001,2026-01-01T12:00:00Z,0,0,a\n999000001,2026-01-01T12:00:00Z,0,0,b\n')
            report = analyze(path)
            self.assertNotIn('duplicate', report['counts'])
            self.assertEqual(report['counts']['malformed_row'], 2)
