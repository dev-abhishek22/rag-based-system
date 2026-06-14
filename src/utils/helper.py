from datetime import date, datetime
from collections import defaultdict
from typing import Optional

def deep_clean(value):
    if isinstance(value, list):
        cleaned = [
            item for raw in value
            if (item := deep_clean(raw)) not in (None, "")
            and not (isinstance(item, (dict, list)) and not item)
        ]
        return cleaned or None

    if isinstance(value, dict):
        cleaned = {
            k: v for k, raw in value.items()
            if (v := deep_clean(raw)) not in (None, "")
            and not (isinstance(v, (dict, list)) and not v)
        }
        return cleaned or None

    if isinstance(value, datetime):
        return value

    return None if value in (None, "") else value

def collect_keys(data, prefix="", keys=None):
    if keys is None:
        keys = defaultdict(set)

    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else key
            keys[path].add(type(value).__name__)
            collect_keys(value, path, keys)

    elif isinstance(data, list):
        for item in data:
            collect_keys(item, prefix, keys)

    return keys

def fmt_date(val) -> Optional[str]:
    if not val:
        return None
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
            try:
                val = datetime.strptime(val, fmt)
                break
            except ValueError:
                continue
        else:
            return val
    if isinstance(val, (datetime, date)):
        return val.strftime("%B %Y")
    return str(val)

def first(*values):
    for value in values:
        if value not in (None, "", "null"):
            return value
    return None