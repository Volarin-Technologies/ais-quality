"""Fetch only the first 5,000 complete rows of an official Zstandard CSV.

Requires zstandard for this developer-only download utility. Runtime does not.
No full archive is downloaded. Output is a prefix, not a representative sample.
"""
import csv
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

URL = 'https://noaaocm.blob.core.windows.net/ais/csv2/csv2024/ais-2024-01-01.csv.zst'


def main():
    import zstandard
    destination = Path(__file__).resolve().parents[1] / 'examples' / 'real-noaa.csv'
    with urllib.request.urlopen(URL, timeout=30) as response:
        with zstandard.ZstdDecompressor().stream_reader(response) as decoded:
            with io.TextIOWrapper(decoded, encoding='utf-8-sig', newline='') as text:
                reader = csv.reader(text)
                rows = [next(reader)]
                for _, row in zip(range(5000), reader):
                    rows.append(row)
    with destination.open('w', encoding='utf-8', newline='') as output:
        csv.writer(output).writerows(rows)
    provenance = dict(source=URL, date_retrieved='2026-10-26', rows=len(rows)-1,
                      selection='First 5000 complete records, unchanged field values; CSV reserialized',
                      sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                      catalog='https://catalog.data.gov/dataset/nationwide-automatic-identification-system-2024',
                      license='https://creativecommons.org/publicdomain/zero/1.0/',
                      credit='USCG Navigation Center, BOEM, NOAA Office for Coastal Management')
    destination.with_suffix('.provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(provenance,indent=2))

if __name__ == '__main__':
    main()
