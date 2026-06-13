from datetime import date, datetime
from collections import defaultdict
from typing import Optional

def deep_clean(value):
    if isinstance(value, list):
        cleaned = []

        for item in value:
            cleaned_item = deep_clean(item)

            if cleaned_item not in (None, '', '0'):
                if isinstance(cleaned_item, dict) and not cleaned_item:
                    continue
                if isinstance(cleaned_item, list) and not cleaned_item:
                    continue

                cleaned.append(cleaned_item)

        return cleaned if cleaned else None

    elif isinstance(value, dict):
        cleaned = {}

        for key, val in value.items():
            cleaned_val = deep_clean(val)

            if cleaned_val not in (None, '', '0'):
                if isinstance(cleaned_val, dict) and not cleaned_val:
                    continue
                if isinstance(cleaned_val, list) and not cleaned_val:
                    continue

                cleaned[key] = cleaned_val

        return cleaned if cleaned else None

    elif isinstance(value, datetime):
        return value

    return None if value in (None, '', '0') else value

def collect_keys(data, prefix="", keys=None):
    if keys is None:
        keys = defaultdict(set)

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key

            keys[current_path].add(type(value).__name__)

            collect_keys(value, current_path, keys)

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

