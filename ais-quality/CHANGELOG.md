# Changelog

## 0.4.0 beta

- Position-conflict warnings and configurable speed/displacement checks.
- Bilingual reports with severity, evidence and review guidance; issues.csv export.
- Explicit UTC assumption for documented timezone-less sources and current NOAA column alias.
- Real 5,000-record NOAA fixture with source, license reference and checksum.
- Local package/CLI, optional ML extra and GitHub Actions matrix.
- Configurable byte/row safeguards, capped HTML sections and staged exports.
- Synthetic sensitivity/false-positive evaluation and reproducible base benchmarks.
- Expanded tests, contribution templates and release documentation.

## 0.3.0

- Optional local Isolation Forest with interval, distance, speed and turn features.
- ML section in HTML/JSON and all-segment scores in ml_segments.csv.
- Deterministic 450-row synthetic demo with injected positional jumps.
- Separate statistical flags from rule failures; skip insufficient datasets.
- Regression tests for continuity, optional dependency and reproducibility.

## 0.2.0

- Automatic recognition of common CSV column aliases and explicit --column mapping.
- Reject ambiguous column mappings instead of silently choosing fields.
- Vessel summary in HTML, JSON and vessels.csv.
- Export flagged_records.csv with issue codes and original record data.
- Neutralize spreadsheet formula prefixes in exported CSV field values.
- Include extra malformed CSV cells when comparing exact duplicate records.
- Add regression coverage for aliases, summaries, exports and malformed rows.

## 0.1.0

- Initial CSV checks, temporal gaps and HTML/JSON reports.
