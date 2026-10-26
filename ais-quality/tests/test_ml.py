import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ais_quality import analyze, timestamp
from ais_ml import distance_nm, segments
from examples.generate_ml_demo import generate

class SegmentTests(unittest.TestCase):
    def record(self, line, minute, lat=0, lon=0):
        return dict(line=line, values=dict(mmsi='999000001', timestamp=f'2026-01-01T00:{minute:02}:00Z', lat=str(lat), lon=str(lon)))

    def test_distance_and_antimeridian(self):
        self.assertAlmostEqual(distance_nm((0, 0), (0, 1)), 60.04, delta=.1)
        self.assertLess(distance_nm((0, 179.9), (0, -179.9)), 13)

    def test_duplicate_time_conflict_and_invalid_breaks(self):
        rows = [self.record(2, 0), self.record(3, 5, 0, .01), self.record(4, 5, 0, .01), self.record(5, 10, 0, .02)]
        self.assertEqual(len(segments(rows, [], timestamp, 30)), 2)
        rows[2]['values']['lon'] = '.5'
        self.assertEqual(segments(rows, [], timestamp, 30), [])
        self.assertEqual(segments([rows[0], rows[1], rows[3]], [{'line': 3, 'code': 'invalid_coordinate'}], timestamp, 30), [])

    def test_gap_breaks_and_short_input(self):
        self.assertEqual(segments([self.record(2, 0), self.record(3, 40)], [], timestamp, 30), [])

    def test_no_optional_import_in_basic_mode(self):
        import sys
        with patch.dict(sys.modules, {'sklearn': None}):
            self.assertEqual(analyze('examples/sample.csv')['ml']['status'], 'disabled')
            with self.assertRaisesRegex(ValueError, 'requires scikit-learn'):
                analyze('examples/sample.csv', ml=True)

@unittest.skipUnless(importlib.util.find_spec('sklearn'), 'Optional ML dependency not installed')
class ModelTests(unittest.TestCase):
    def test_small_input_and_bad_sensitivity(self):
        self.assertEqual(analyze('examples/sample.csv', ml=True)['ml']['status'], 'insufficient_data')
        for value in [0, .6, float('nan')]:
            with self.assertRaises(ValueError):
                analyze('examples/sample.csv', ml=True, contamination=value)

    def test_reproducible_and_injected_jump_is_ranked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'demo.csv'
            generate(path)
            result = analyze(path, ml=True)
            again = analyze(path, ml=True)
            self.assertEqual(result['ml'], again['ml'])
            self.assertEqual(result['flagged_rows'], 4)
            self.assertEqual(result['ml']['eligible_segments'], 447)
            self.assertGreater(len(result['ml']['alerts']), 0)
            top_lines = {a['line'] for a in result['ml']['alerts'][:6]}
            self.assertIn(82, top_lines)  # first injected jump ends at CSV line 82
            self.assertTrue(all(a['anomaly_score'] > 0 for a in result['ml']['alerts']))
