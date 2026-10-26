# Validation record · 0.4.0 beta

Executed locally on 2026-10-26. These checks are evidence of reproducible behavior, not production certification.

## Tests and installation

28 tests cover schema/mapping, duplicates, malformed rows, coordinates, MMSI, timezone handling, gaps, conflicting positions, movement thresholds, exports and CSV escaping, staged write failure, input overwrite protection, resource limits, optional dependencies, spherical distance, ML reproducibility and fixture checksum.

With scikit-learn 1.8.0 on Python 3.12.14, all 28 pass. In a fresh venv without ML packages, 26 pass and 2 model tests skip. A wheel was installed into a fresh venv and the installed CLI was run from outside the source tree. Other Python/OS combinations are not claimed as locally tested. GitHub's multi-version matrix is configured but has not run here.

## Real-data compatibility smoke test

Source and permission: see [SOURCES.md](../SOURCES.md) and the fixture provenance JSON. Input is the first 5,000 records of January 1, 2024 from NOAA, not a random or representative sample. Offsets are absent; explicit --assume-utc follows NOAA's UTC field documentation.

Observed: 5,000 records, 4,614 structurally valid distinct MMSIs, 386 eligible movement segments, 1 flagged source row and 12 ML alerts at contamination 0.03. One row crosses both configured speed and distance review thresholds. Its segment endpoints and evidence are in the report. No ground-truth adjudication was performed, so these are findings, not confirmed provider errors. This source was already filtered by NOAA; no result should be generalized to raw AIS streams.

Reproduce:

```bash
python3 ais_quality.py examples/real-noaa.csv --assume-utc --ml --output reports-noaa
```

## Synthetic ML experiment

Three seeds, two scenarios (clean / injected) and three contamination values: 18 fits. Each scenario contains 450 records and 447 eligible segments. The injected case has two displaced positions, making four jump endpoint segments: CSV lines 82, 83, 262, 263. Labels cover only direct jump segments; subsequent speed-change effects are counted as false positives. This simple definition is documented so readers can inspect and challenge it.

All fits use the SAME file for fitting and scoring; this is not held-out performance. Seed 42 results:

| Scenario | Sensitivity | Alerts | TP | FP | Recall on four labels | False-positive rate |
| --- | --- | --- | --- | --- | --- | --- |
| Clean | 0.01 | 5 | 0 | 5 | N/A | 1.12% |
| Clean | 0.03 | 14 | 0 | 14 | N/A | 3.13% |
| Clean | 0.1 | 45 | 0 | 45 | N/A | 10.07% |
| Injected | 0.01 | 5 | 4 | 1 | 1.0 | 0.23% |
| Injected | 0.03 | 14 | 4 | 10 | 1.0 | 2.26% |
| Injected | 0.1 | 45 | 4 | 41 | 1.0 | 9.26% |

The clean scenario still triggers alerts. That is an expected consequence of specifying an outlier fraction, and a reason to keep ML optional. These examples are deliberately simple. They do not establish precision/recall on operational AIS data or prove generalization across vessel types. All seeds and results: [ml-evaluation.json](ml-evaluation.json).

Reproduce with ML dependencies installed: `python3 tools/evaluate_ml.py`.

## Resource benchmark

Fresh Linux process per size; valid synthetic records, basic mode, analysis and all exports. Peak RSS includes data generation and interpreter. Input has four narrow columns, mostly regular movement and no flagged rows; wide or heavily flagged files can cost substantially more memory. ML training cost is not covered by this benchmark.

| Records | Analysis (s) | Exports (s) | Peak RSS (MiB) |
| --- | --- | --- | --- |
| 10,000 | 0.146 | 0.075 | 37.9 |
| 50,000 | 0.885 | 0.411 | 135.3 |
| 100,000 | 1.775 | 0.757 | 259.1 |

Environment: Python 3.12.14, Linux-6.18.55-x86_64-with-glibc2.39. Timings are a single local run, not a service-level guarantee. Source metrics: [benchmark.json](benchmark.json). Reproduce: `python3 tools/benchmark.py`.

Default safeguards stop above 100,000 rows or 100,000,000 input bytes. These guardrails are not guarantees against all high-memory inputs. Limits can be explicitly raised. The algorithm remains in-memory and is not suitable for arbitrary daily AIS archives without extracting smaller subsets.

Additional clean ML environment: wheel plus optional dependencies installed in a separate fresh venv; scikit-learn 1.9.1. All 28 source tests passed and the installed CLI processed the 450-row demo from outside the source directory.

HTML visual QA: local Chromium rendering at desktop 1440px and mobile 390px; no document horizontal overflow or page errors in the synthetic report. The real report shows its 500-entry display limit. The README image is a capture of the synthetic report.
