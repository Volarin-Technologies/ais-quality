import tempfile
import unittest
from pathlib import Path
from ais_quality import analyze, render

class QualityTests(unittest.TestCase):
    def check_csv(self, text, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.csv'
            path.write_text(text, encoding='utf-8')
            return analyze(path, **kwargs)

    def test_demo_counts(self):
        result = analyze('examples/sample.csv')
        self.assertEqual(result['total_rows'], 7)
        self.assertEqual(result['flagged_rows'], 4)
        self.assertEqual(result['counts'], {'duplicate': 1, 'invalid_coordinate': 2, 'missing_field': 1, 'invalid_timestamp': 1})
        self.assertEqual(result['gaps'][0]['minutes'], 55)

    def test_sort_timezone_dedup_and_boundary(self):
        result = self.check_csv('mmsi,timestamp,lat,lon\n999000001,2026-01-01T13:00:00Z,0,0\n999000001,2026-01-01T09:00:00-03:00,0,0\n999000001,2026-01-01T12:00:00Z,1,1\n', gap_minutes=60)
        self.assertEqual(result['gaps'], [])
        self.assertEqual(len(self.check_csv('mmsi,timestamp,lat,lon\n999000001,2026-01-01T13:00:00Z,0,0\n999000001,2026-01-01T12:00:00Z,0,0\n')['gaps']), 1)

    def test_nonfinite_and_naive_time(self):
        result = self.check_csv('mmsi,timestamp,lat,lon\n000000000,2026-01-01T12:00:00,NaN,inf\n')
        self.assertEqual(result['counts']['invalid_coordinate'], 2)
        self.assertEqual(result['counts']['invalid_timestamp'], 1)
        self.assertEqual(result['counts']['invalid_mmsi'], 1)

    def test_schema_and_threshold(self):
        for text in ['', 'mmsi,lat,lon\n', 'mmsi,timestamp,lat,lon,lat\n']:
            with self.assertRaises(ValueError):
                self.check_csv(text)
        with self.assertRaises(ValueError):
            analyze('examples/sample.csv', float('nan'))

    def test_empty_dataset(self):
        result = self.check_csv('mmsi,timestamp,lat,lon\n')
        self.assertEqual(result['total_rows'], 0)

    def test_ragged_and_html_escape(self):
        result = self.check_csv('mmsi,timestamp,lat,lon\n<script>,bad,0,0,extra\n')
        self.assertIn('malformed_row', result['counts'])
        self.assertNotIn('<script>', render(result))

if __name__ == '__main__':
    unittest.main()
