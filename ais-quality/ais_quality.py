"""AIS CSV quality checks. Python 3.10+, optional local ML."""
import argparse
import csv
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

__version__ = '0.4.0'
REQUIRED = ('mmsi', 'timestamp', 'lat', 'lon')
ALIASES = {
    'mmsi': ('mmsi', 'vessel_mmsi'),
    'timestamp': ('timestamp', 'basedatetime', 'base_date_time', 'datetime', 'time'),
    'lat': ('lat', 'latitude'),
    'lon': ('lon', 'longitude', 'lng'),
}


def resolve_columns(headers, overrides=None):
    overrides = overrides or {}
    if set(overrides) - set(REQUIRED):
        raise ValueError('Unknown canonical field in column mapping')
    if len(headers) != len(set(headers)):
        raise ValueError('Duplicate CSV headers')
    mapping = {}
    for field in REQUIRED:
        if field in overrides:
            candidates = [h for h in headers if h == overrides[field]]
        else:
            candidates = [h for h in headers if h.strip().lower() in ALIASES[field]]
        if not candidates:
            raise ValueError('Missing column: ' + field)
        if len(candidates) > 1:
            raise ValueError('Ambiguous columns for ' + field + '; use --column')
        mapping[field] = candidates[0]
    if len(set(mapping.values())) != len(REQUIRED):
        raise ValueError('Each canonical field must map to a distinct column')
    return mapping


def parse_columns(items):
    mapping = {}
    for item in items:
        key, separator, value = item.partition('=')
        if not separator or key not in REQUIRED or not value or key in mapping:
            raise ValueError('Use --column FIELD=CSV_HEADER once per field')
        mapping[key] = value
    return mapping


def timestamp(value, assume_utc=False):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        if not assume_utc:
            raise ValueError('Timezone required (or explicitly enable --assume-utc)')
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def analyze(path, gap_minutes=30, delimiter=',', columns=None, ml=False, contamination=0.03, max_speed_knots=60, max_jump_nm=20,
            assume_utc=False, max_rows=100000, max_bytes=100000000, language='en'):
    if not math.isfinite(gap_minutes) or gap_minutes <= 0:
        raise ValueError('gap_minutes must be positive and finite')
    if language not in ('en', 'pt'):
        raise ValueError('Language must be en or pt')
    for name, value in [('max_speed_knots', max_speed_knots), ('max_jump_nm', max_jump_nm)]:
        if not math.isfinite(value) or value <= 0:
            raise ValueError(name + ' must be positive and finite')
    if max_rows < 1 or max_bytes < 1:
        raise ValueError('Resource limits must be positive')
    if Path(path).stat().st_size > max_bytes:
        raise ValueError('Input exceeds max_bytes; increase the limit explicitly')
    parse_time = lambda value: timestamp(value, assume_utc)
    issues, seen, tracks = [], {}, defaultdict(set)
    total = 0
    records, vessel_rows = [], defaultdict(list)
    def issue(line, code, detail):
        issues.append(dict(line=line, code=code, detail=detail))
    with open(path, encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source, delimiter=delimiter, strict=True)
        headers = reader.fieldnames or []
        mapping = resolve_columns(headers, columns)
        for row in reader:
            total += 1
            if total > max_rows:
                raise ValueError('Input exceeds max_rows; increase the limit explicitly')
            line = reader.line_num
            if None in row or any(v is None for v in row.values()):
                issue(line, 'malformed_row', 'Column count differs from header')
            values = {k: (row.get(mapping[k]) or '').strip() for k in REQUIRED}
            record = dict(line=line, values=values)
            records.append(record)
            issue_start = len(issues)
            for key, value in values.items():
                if not value:
                    issue(line, 'missing_field', key)
            signature = tuple((h, row.get(h)) for h in headers) + (tuple(row.get(None, [])),)
            if signature in seen:
                issue(line, 'duplicate', f'Exact row duplicate of line {seen[signature]}')
            else:
                seen[signature] = line
            mmsi = values['mmsi']
            valid_mmsi = len(mmsi) == 9 and mmsi.isascii() and mmsi.isdigit() and mmsi != '000000000'
            if valid_mmsi:
                vessel_rows[mmsi].append(line)
            if mmsi and not valid_mmsi:
                issue(line, 'invalid_mmsi', mmsi)
            for key, limit in [('lat', 90), ('lon', 180)]:
                if values[key]:
                    try:
                        number = float(values[key])
                        if not math.isfinite(number) or not -limit <= number <= limit:
                            raise ValueError()
                    except ValueError:
                        issue(line, 'invalid_coordinate', key + '=' + values[key])
            if values['timestamp']:
                try:
                    dt = parse_time(values['timestamp'])
                    if valid_mmsi:
                        tracks[mmsi].add(dt)
                except (ValueError, OverflowError):
                    issue(line, 'invalid_timestamp', values['timestamp'])
            if len(issues) > issue_start:
                record['original'] = row
    from ais_ml import segments
    positions = defaultdict(list)
    bad_lines = {i['line'] for i in issues if i['code'] != 'duplicate'}
    for record in records:
        if record['line'] not in bad_lines:
            v = record['values']
            positions[(v['mmsi'], parse_time(v['timestamp']))].append(record)
    for (mmsi, dt), group in positions.items():
        if len({(float(r['values']['lat']), float(r['values']['lon'])) for r in group}) > 1:
            lines = [r['line'] for r in group]
            for record in group:
                issue(record['line'], 'position_conflict', f'MMSI {mmsi}, {dt.isoformat()}, lines {lines}')
    movement = segments(records, issues, parse_time, gap_minutes)
    for segment in movement:
        evidence = f"previous_line={segment['previous_line']}; interval_minutes={segment['interval_minutes']:.6g}; distance_nm={segment['distance_nm']:.6g}; speed_knots={segment['speed_knots']:.6g}"
        if segment['speed_knots'] > max_speed_knots:
            issue(segment['line'], 'speed_exceeded', f'{evidence}; threshold_knots={max_speed_knots:g}')
        if segment['distance_nm'] > max_jump_nm:
            issue(segment['line'], 'position_jump', f'{evidence}; threshold_nm={max_jump_nm:g}')
    # Recover source columns for newly flagged rows without retaining every original row.
    new_lines = {i['line'] for i in issues} - {r['line'] for r in records if 'original' in r}
    if new_lines:
        with open(path, encoding='utf-8-sig', newline='') as source:
            reader = csv.DictReader(source, delimiter=delimiter, strict=True)
            by_record = {r['line']: r for r in records if r['line'] in new_lines}
            for row in reader:
                if reader.line_num in by_record:
                    by_record[reader.line_num]['original'] = row
    gaps = []
    for mmsi, times in sorted(tracks.items()):
        times = sorted(times)
        for start, end in zip(times, times[1:]):
            minutes = (end - start).total_seconds() / 60
            if minutes > gap_minutes:
                gaps.append(dict(mmsi=mmsi, start=start.isoformat(), end=end.isoformat(), minutes=minutes))
    by_line = defaultdict(list)
    for entry in issues:
        by_line[entry['line']].append(entry)
    flagged = len(by_line)
    flagged_records = [dict(record, issue_codes=sorted({i['code'] for i in by_line[record['line']]}))
                       for record in records if record['line'] in by_line]
    gap_counts = Counter(g['mmsi'] for g in gaps)
    vessels = []
    for mmsi, lines in sorted(vessel_rows.items()):
        times = sorted(tracks[mmsi])
        vessels.append(dict(mmsi=mmsi, total_rows=len(lines),
                            flagged_rows=sum(line in by_line for line in lines),
                            unique_timestamps=len(times),
                            first_timestamp=times[0].isoformat() if times else None,
                            last_timestamp=times[-1].isoformat() if times else None,
                            gap_count=gap_counts[mmsi]))
    ml_result = dict(status='disabled', alerts=[], scored_segments=[])
    if ml:
        from ais_ml import detect
        ml_result = detect(records, issues, parse_time, gap_minutes, contamination)
    from ais_report import enrich
    issues = enrich(issues, language)
    return dict(language=language, settings=dict(max_speed_knots=max_speed_knots,
                max_jump_nm=max_jump_nm, assume_utc=assume_utc, max_rows=max_rows, max_bytes=max_bytes),
                movement_segments=movement, ml=ml_result, version=__version__, column_mapping=mapping, vessels=vessels,
                flagged_records=flagged_records, source_columns=headers, source=Path(path).name, total_rows=total, flagged_rows=flagged,
                rows_without_flags=total - flagged, gap_threshold_minutes=gap_minutes,
                counts=dict(Counter(i['code'] for i in issues)), issues=issues, gaps=gaps)


def render(report):
    from ais_report import render_html
    return render_html(report)


def spreadsheet_safe(value):
    # Preserve raw values in JSON; neutralize spreadsheet formulas in CSV exports.
    value = '' if value is None else str(value)
    if value.lstrip().startswith(('=', '+', '-', '@')) or value.startswith(('\t', '\r', '\n')):
        return "'" + value
    return value


def _write_reports(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    (output / 'report.html').write_text(render(report), encoding='utf-8')
    with (output / 'flagged_records.csv').open('w', encoding='utf-8', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['csv_line', 'issue_codes', *REQUIRED, 'original_record_json'])
        for record in report['flagged_records']:
            writer.writerow([record['line'], '|'.join(record['issue_codes']),
                             *(spreadsheet_safe(record['values'][key]) for key in REQUIRED),
                             json.dumps(record['original'], ensure_ascii=False)])
    with (output / 'issues.csv').open('w', encoding='utf-8', newline='') as target:
        fields = ['line', 'code', 'severity', 'title', 'detail', 'recommendation']
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: spreadsheet_safe(v) for k, v in issue.items()} for issue in report['issues'])
    with (output / 'ml_segments.csv').open('w', encoding='utf-8', newline='') as target:
        fields = ['mmsi', 'line', 'previous_line', 'timestamp', 'interval_minutes', 'distance_nm',
                  'speed_knots', 'speed_change_knots', 'turn_degrees', 'anomaly_score', 'flagged']
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report['ml']['scored_segments'])
    with (output / 'vessels.csv').open('w', encoding='utf-8', newline='') as target:
        fields = ['mmsi', 'total_rows', 'flagged_rows', 'unique_timestamps',
                  'first_timestamp', 'last_timestamp', 'gap_count']
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report['vessels'])



REPORT_FILES = ('report.html', 'report.json', 'issues.csv', 'flagged_records.csv', 'vessels.csv', 'ml_segments.csv')


def export_reports(report, output):
    """Stage all outputs before replacing individual files; unrelated files remain."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ais-quality-', dir=output) as stage:
        _write_reports(report, stage)
        for name in REPORT_FILES:
            os.replace(Path(stage) / name, output / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=['en', 'pt'], default='en')
    parser.add_argument('--max-speed-knots', type=float, default=60)
    parser.add_argument('--max-jump-nm', type=float, default=20)
    parser.add_argument('--assume-utc', action='store_true', help='Treat timezone-less input timestamps as UTC')
    parser.add_argument('--max-rows', type=int, default=100000)
    parser.add_argument('--max-bytes', type=int, default=100000000)
    parser.add_argument('--ml', action='store_true', help='Enable optional local Isolation Forest')
    parser.add_argument('--contamination', type=float, default=0.03, help='Expected outlier fraction for ML (0, 0.5]')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--column', action='append', default=[], metavar='FIELD=CSV_HEADER')
    parser.add_argument('csv', type=Path)
    parser.add_argument('--gap-minutes', type=float, default=30)
    parser.add_argument('--delimiter', default=',')
    parser.add_argument('--output', type=Path, default=Path('reports'))
    args = parser.parse_args()
    try:
        if len(args.delimiter) != 1:
            raise ValueError('Delimiter must be a single character')
        if args.csv.resolve() in {(args.output / name).resolve() for name in REPORT_FILES}:
            raise ValueError('Output would overwrite the input file; choose another output directory')
        report = analyze(args.csv, args.gap_minutes, args.delimiter, parse_columns(args.column), args.ml, args.contamination,
                         args.max_speed_knots, args.max_jump_nm, args.assume_utc,
                         args.max_rows, args.max_bytes, args.language)
        export_reports(report, args.output)
    except (ValueError, OSError, csv.Error, OverflowError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(f"{report['total_rows']} rows | {report['flagged_rows']} flagged | {len(report['gaps'])} gaps")
    if args.ml:
        print(f"ML: {report['ml']['status']} | {len(report['ml']['alerts'])} flagged segments")
    print(args.output / 'report.html')


if __name__ == '__main__':
    main()
