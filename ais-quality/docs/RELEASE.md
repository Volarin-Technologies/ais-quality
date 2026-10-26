# Release 0.4.0 beta

## Completed locally

- Rules, conflict detection, movement limits and bilingual reports implemented.
- Provenance and checksum for real NOAA fixture retained.
- Synthetic ML evaluation and base performance measurements recorded.
- 28 tests: all pass with the available ML environment; 26 pass and 2 ML tests skip in a fresh dependency-free environment.
- Wheel built and installed in a new virtual environment; installed CLI executed outside the source directory.
- Source and examples documented; contributing and issue/PR templates included.
- GitHub Actions configuration included for base and ML jobs on Python 3.10, 3.12 and 3.13.

## Requires the actual repository

1. Upload/extract the project CONTENTS into the intended public repository (pyproject.toml at repository root).
2. Inspect and run GitHub Actions. The workflow has not run on GitHub in this session.
3. Replace placeholder repository links in LINKEDIN.md. Add the actual URL in the repository About section.
4. Review the README screenshot and licensing. Keep SOURCES.md and dataset provenance with the real fixture.
5. Create a v0.4.0 release/tag after the repository checks pass.
6. Invite a small number of maritime data users to try their own files and report reproducible issues.

No repository or package-index publication, hosting, account creation or external messages were performed. PyPI name availability has not been checked; distribution name here is for local installation.

## Honest launch claims

Say: local AIS CSV auditing, configurable review rules, optional exploratory ML, bilingual reports, reproducible examples and a small real-data compatibility test.

Do not claim: production certification, proven real-world detection accuracy, real-time tracking, pretrained maritime intelligence or universal vessel-speed limits. Large-file operation remains in memory and is bounded by default.

Additional clean ML environment: wheel plus optional dependencies installed in a separate fresh venv; scikit-learn 1.9.1. All 28 source tests passed and the installed CLI processed the 450-row demo from outside the source directory.

HTML visual QA: local Chromium rendering at desktop 1440px and mobile 390px; no document horizontal overflow or page errors in the synthetic report. The real report shows its 500-entry display limit. The README image is a capture of the synthetic report.
