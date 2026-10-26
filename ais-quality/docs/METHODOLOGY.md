# Methodology and interpretation

## Rules

Schema errors stop execution. Row errors include missing required values, malformed CSV shape, nonfinite/out-of-range coordinates, invalid timestamps and malformed nine-digit MMSIs. A valid MMSI shape does not verify assignment in a registry. Duplicate rows compare all source fields (including extra malformed cells), with original whitespace preserved.

Positions are grouped by MMSI and UTC time. Distinct numeric positions at the same time produce `position_conflict` warnings on all participating structurally valid rows. Conflicts break trajectory continuity; no arbitrary position is selected. Exact-time identical positions are collapsed for movement.

Temporal gaps sort valid timestamps for each structurally valid MMSI and use a strict `>` threshold, even if coordinates are invalid. Gap events are separate from flagged rows. Irregular sampling, reception coverage and filtering can all create gaps.

Movement uses spherical haversine distance (earth radius 3440.065 nautical miles), divided by elapsed hours for estimated knots. This is straight-line displacement, not travelled route length or AIS-reported SOG. Segments across intervals greater than --gap-minutes are excluded. Invalid positions and conflicts reset continuity. Invalid timestamps cannot be placed and are skipped. Movement warning limits default to 60 knots and 20 nautical miles; these are configurable review thresholds, not universal physical limits. Longer legitimate movements can exceed them.

Flags reference physical ending CSV lines; headers count and multiline quoted records end on their last physical line. An affected row counts once regardless of number of rules. Summaries include duplicates in raw row counts. Invalid MMSIs are excluded from vessel groups but remain in rule outputs.

## Machine learning

Optional Isolation Forest uses 200 trees, random seed 42 and one worker. It pools eligible segments across vessels. Features are elapsed minutes, spherical nautical-mile distance, estimated speed in knots, absolute speed change in knots, and bearing change in degrees (shortest angle). Speed change is not acceleration. First-segment derivative features and turns involving stationary positions are zero. Raw features are used; correlated features may influence scores.

At least 30 eligible segments are required (engineering guard, not a statistical sufficiency guarantee). Structural rule failures and conflicts are excluded. Speed/jump rule warnings remain eligible so ML can examine the same unusual movements independently. Intervals above the gap limit reset history.

The model fits and scores the SAME input file. This is exploratory outlier detection, not a pretrained maritime model or independent validation. Different vessel types, modes and sampling rates are pooled, so unusual but valid behavior may be flagged. --contamination selects a threshold based on an expected outlier fraction, which can create alerts even on entirely normal synthetic tracks. Ties can alter the count. No guaranteed number of alerts exists.

anomaly_score = negative decision_function; positive values are flagged and larger values are more unusual relative to this fit. Scores are not probabilities, comparable across files, feature attributions, or evidence of bad intent. Fixed seeds reproduce results in a fixed environment; library versions can change results. Reports record the library version, settings and sample count.

[Isolation Forest reference](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).

## Resources and exports

In-memory processing retains canonical records, duplicate signatures, trajectory samples and findings. Original extra fields are retained only for flagged records; a second CSV pass recovers newly flagged source rows. Byte and row safeguards reject oversized inputs instead of silently sampling. An exceptionally wide or heavily flagged dataset may use much more memory than the benchmark. This is not a streaming solution.

The HTML displays at most 500 entries per section and explicitly notes truncation. JSON and CSV preserve complete results. Six report files are staged before individual atomic replacements; the whole set is not transactionally atomic. CSV values that might become spreadsheet formulas are prefixed with an apostrophe. JSON preserves raw source values. Files are processed locally, but publishing an export can reveal their contents. No data correction or deletion is automatic.
