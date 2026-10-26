"""Synthetic, in-file diagnostic experiment; not held-out real-world accuracy."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ais_quality import analyze
from examples.generate_ml_demo import generate


def run():
    results=[]
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'tracks.csv'
        for seed in (42, 43, 44):
            for injected in (False, True):
                generate(path, inject=injected, seed=seed)
                labels={82,83,262,263} if injected else set()
                for sensitivity in (.01,.03,.10):
                    report=analyze(path, ml=True, contamination=sensitivity)
                    scored=report['ml']['scored_segments']
                    flagged={s['line'] for s in scored if s['flagged']}
                    tp=len(flagged & labels); fp=len(flagged-labels)
                    normal=len(scored)-len(labels)
                    results.append(dict(seed=seed,injected=injected,contamination=sensitivity,
                        segments=len(scored), flagged=len(flagged),true_positive=tp,false_positive=fp,
                        false_negative=len(labels-flagged),precision=tp/len(flagged) if flagged else None,
                        recall=tp/len(labels) if labels else None,false_positive_rate=fp/normal))
    return dict(protocol='In-file unsupervised fit and score, three seeds, clean and injected synthetic tracks; labels cover only four jump endpoint segments. Nearby derivative effects count as false positives.',
                labels=[82,83,262,263], results=results)

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
