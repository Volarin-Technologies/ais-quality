import unittest
from ais_quality import analyze, render

class ReportTests(unittest.TestCase):
    def test_table_limit_keeps_full_data(self):
        result=analyze('examples/sample.csv')
        entry=result['issues'][0]
        result['issues']=[dict(entry,line=n) for n in range(501)]
        result['source']='<script>alert(1)</script>'
        html=render(result)
        self.assertIn('Showing first 500 entries',html)
        self.assertNotIn('<script>',html)
        self.assertEqual(len(result['issues']),501)
