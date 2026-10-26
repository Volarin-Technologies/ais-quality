# Data sources and permissions

## Real NOAA fixture

- Provider: NOAA Office for Coastal Management / MarineCadastre; credit US Coast Guard Navigation Center and Bureau of Ocean Energy Management.
- Dataset: Nationwide Automatic Identification System 2024.
- Catalog: https://catalog.data.gov/dataset/nationwide-automatic-identification-system-2024
- Official metadata: https://www.fisheries.noaa.gov/inport/item/73064
- Official archive index: https://noaaocm.blob.core.windows.net/ais/csv2/csv2024/index.html
- File: https://noaaocm.blob.core.windows.net/ais/csv2/csv2024/ais-2024-01-01.csv.zst
- Retrieval: 2026-10-26.
- Dataset catalog license field: CC0, https://creativecommons.org/publicdomain/zero/1.0/ (checked 2026-10-26). Catalog also contains a contradictory `accessLevel: non-public` label; the official downloadable resource was publicly accessible without authentication. Use/redistribution basis here is the catalog's explicit CC0 license, not mere accessibility.
- Fixture: `examples/real-noaa.csv`, first 5,000 complete CSV records, reserialized with Python csv; original header and field values retained. No randomized selection, denoising, identity replacement or timestamp conversion.
- Exact fixture checksum and source are in `examples/real-noaa.provenance.json`.
- Timestamp interpretation: the NOAA [data dictionary](https://coast.noaa.gov/data/marinecadastre/ais/data-dictionary.pdf) documents BaseDateTime as UTC. The new snake_case field is `base_date_time`. The importer uses explicit `--assume-utc` when offsets are absent.
- Reproduce: install the developer-only `zstandard` package and run `python3 tools/fetch_noaa_sample.py`. This streams the beginning of the archive instead of downloading a whole daily file. Runtime auditing does not use the network.

This is a small prefix dominated by many distinct vessels with short observed histories. It is a compatibility smoke test, not a representative benchmark of maritime operations, an independently verified truth set, or an evaluation of ML accuracy. No agency endorsement is implied. The sample retains real MMSIs and vessel metadata exactly as publicly distributed by the provider.

## Synthetic fixtures

`sample.csv`, `provider-columns.csv` and `ml-demo.csv` are fictional examples. The ML generator uses reserved-for-demonstration fictional identifiers in this project; no registry assignment is asserted. `examples/generate_ml_demo.py` reproduces the ML data using a fixed seed. `tools/evaluate_ml.py` generates clean and injected variants with seeds 42, 43 and 44.

Code is MIT. The real dataset is attributed separately under the catalog's CC0 declaration.
