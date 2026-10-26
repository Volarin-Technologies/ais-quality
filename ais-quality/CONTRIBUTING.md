# Contributing

Thank you for helping improve AIS data quality.

1. Open an issue describing a reproducible problem or proposal. Use the templates.
2. Fork the repository and create a focused branch.
3. Add or update meaningful tests and documentation when behavior changes.
4. Run `python3 -m unittest discover -s tests -v` from the repository root. For ML changes, install `.[ml]` and run the complete suite and evaluation utility.
5. Submit a pull request explaining the problem, behavior and validation.

Prefer small changes. Preserve a dependency-free basic mode, deterministic tests, explicit configuration and separation of rule failures from statistical alerts. Never silently infer missing source values. Do not add network calls to analysis or report rendering.

Use synthetic minimal reproductions. Do not attach private customer data, credentials or restricted AIS extracts. New real fixtures need a primary source, use permission/license, extraction method and checksum. Changes to ML need false-positive analysis, not just successful detection of injected anomalies.

Code contributions are under MIT. Dataset licenses remain separate. Treat other contributors respectfully and keep discussions focused on technical evidence. No response-time commitment is currently offered.
