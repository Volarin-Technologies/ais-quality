"""Optional local, exploratory trajectory anomaly detection."""
import math
from collections import defaultdict

FEATURES = ['interval_minutes', 'distance_nm', 'speed_knots', 'speed_change_knots', 'turn_degrees']
MIN_SEGMENTS = 30


def distance_nm(a, b):
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat, dlon = lat2 - lat1, math.radians(b[1] - a[1])
    h = math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon / 2)**2
    return 3440.065 * 2 * math.asin(math.sqrt(min(1, max(0, h))))


def bearing(a, b):
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlon = math.radians(b[1] - a[1])
    return math.degrees(math.atan2(math.sin(dlon)*math.cos(lat2),
                        math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(dlon))) % 360


def segments(records, issues, parse_timestamp, gap_minutes):
    # Invalid rows and conflicting simultaneous positions break trajectory continuity.
    invalid = {i['line'] for i in issues if i['code'] not in ('duplicate', 'speed_exceeded', 'position_jump')}
    tracks = defaultdict(lambda: defaultdict(list))
    for record in records:
        v = record['values']
        try:
            dt = parse_timestamp(v['timestamp'])
        except (ValueError, OverflowError):
            continue
        mmsi = v['mmsi']
        if len(mmsi) != 9 or not mmsi.isascii() or not mmsi.isdigit() or mmsi == '000000000':
            continue
        point = None if record['line'] in invalid else (float(v['lat']), float(v['lon']))
        tracks[mmsi][dt].append((record['line'], point))
    result = []
    for mmsi, observations in sorted(tracks.items()):
        previous = None
        previous_speed = previous_bearing = None
        for dt, group in sorted(observations.items()):
            points = {point for _, point in group}
            if None in points or len(points) != 1:
                previous = None
                previous_speed = previous_bearing = None
                continue
            line, point = min(group, key=lambda item: item[0])
            if previous is not None:
                prev_dt, prev_line, prev_point = previous
                minutes = (dt - prev_dt).total_seconds() / 60
                if minutes > gap_minutes:
                    previous_speed = previous_bearing = None
                else:
                    distance = distance_nm(prev_point, point)
                    speed = distance / (minutes / 60)
                    heading = bearing(prev_point, point) if distance > 1e-6 else None
                    change = abs(speed - previous_speed) if previous_speed is not None else 0.0
                    turn = abs((heading - previous_bearing + 180) % 360 - 180) if heading is not None and previous_bearing is not None else 0.0
                    result.append(dict(mmsi=mmsi, line=line, previous_line=prev_line,
                                       timestamp=dt.isoformat(), interval_minutes=minutes,
                                       distance_nm=distance, speed_knots=speed,
                                       speed_change_knots=change, turn_degrees=turn))
                    previous_speed, previous_bearing = speed, heading
            previous = dt, line, point
    return result


def detect(records, issues, parse_timestamp, gap_minutes, contamination=0.03):
    if not math.isfinite(contamination) or not 0 < contamination <= 0.5:
        raise ValueError('ML contamination must be in (0, 0.5]')
    try:
        import sklearn
        from sklearn.ensemble import IsolationForest
    except ImportError as exc:
        raise ValueError('ML requires scikit-learn: python3 -m pip install -r requirements-ml.txt') from exc
    samples = segments(records, issues, parse_timestamp, gap_minutes)
    result = dict(status='insufficient_data', model='IsolationForest', sklearn_version=sklearn.__version__,
                  seed=42, contamination=contamination, min_segments=MIN_SEGMENTS,
                  features=FEATURES, eligible_segments=len(samples), alerts=[], scored_segments=[])
    if len(samples) < MIN_SEGMENTS:
        return result
    matrix = [[s[f] for f in FEATURES] for s in samples]
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=42, n_jobs=1)
    model.fit(matrix)
    decisions = model.decision_function(matrix)
    result.update(status='completed', decision_threshold=0.0)
    for sample, decision in zip(samples, decisions):
        sample = dict(sample, anomaly_score=-float(decision), flagged=bool(decision < 0))
        result['scored_segments'].append(sample)
        if sample['flagged']:
            result['alerts'].append(sample)
    result['alerts'].sort(key=lambda s: s['anomaly_score'], reverse=True)
    return result
