"""Reproducible synthetic tracks; not real vessels or a performance benchmark."""
import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def generate(path, inject=True, seed=42):
    rng = random.Random(seed)
    with Path(path).open('w', newline='', encoding='utf-8') as output:
        writer = csv.writer(output)
        writer.writerow(['mmsi', 'timestamp', 'lat', 'lon'])
        for vessel in range(3):
            lat, lon = -24 + vessel * .15, -46 + vessel * .2
            dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
            for i in range(150):
                dt += timedelta(minutes=5 + rng.uniform(-.5, .5))
                lat += .003 + rng.uniform(-.0003, .0003)
                lon += .004 + .0005 * math.sin(i / 10) + rng.uniform(-.0003, .0003)
                # Two isolated synthetic position jumps, followed by a return.
                jump = .8 if inject and i == 80 and vessel == 0 else 0
                jump = jump or (.5 if inject and i == 110 and vessel == 1 else 0)
                writer.writerow([999000001 + vessel, dt.isoformat(), f'{lat + jump:.7f}', f'{lon:.7f}'])

if __name__ == '__main__':
    generate(Path(__file__).with_name('ml-demo.csv'))
