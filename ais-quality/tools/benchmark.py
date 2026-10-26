"""Measure base analysis+exports in a fresh process per size (Linux peak RSS)."""
import argparse
import csv
import json
import platform
import resource
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ais_quality import analyze, export_reports


def worker(n):
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)/'input.csv'
        start=datetime(2026,1,1,tzinfo=timezone.utc)
        with p.open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(['mmsi','timestamp','lat','lon'])
            for i in range(n):
                writer.writerow([999000001+i//1000,(start+timedelta(minutes=i%1000)).isoformat(),-24+(i%1000)*.0001,-46])
        t=time.perf_counter();r=analyze(p);analysis=time.perf_counter()-t
        t=time.perf_counter();export_reports(r,Path(directory)/'out');exports=time.perf_counter()-t
        return dict(rows=n,input_bytes=p.stat().st_size,analysis_seconds=round(analysis,3),export_seconds=round(exports,3),
                    peak_rss_mib=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1),flagged_rows=r['flagged_rows'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',type=int);args=parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker)))
    else:
        results=[]
        for size in [10000,50000,100000]:
            results.append(json.loads(subprocess.check_output([sys.executable,__file__,'--worker',str(size)])))
        print(json.dumps(dict(python=platform.python_version(),platform=platform.platform(),mode='base, synthetic valid rows, analysis plus all exports; peak RSS includes input generation',results=results),indent=2))
