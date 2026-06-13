import json
import re
from typing import Optional
import bleach
import markdownify


def strip_html(val) -> Optional[str]:
    if not val or not isinstance(val, str):
        return None
    text = markdownify.markdownify(val, heading_style="ATX", strip=["a", "img"])
    text = bleach.clean(text, tags=[], strip=True)
    text = re.sub(r" +", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("&amp;", "&")
    return text.strip() or None


def parse_json(val):
    if not val or not isinstance(val, str):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, ValueError):
        return val


def clean_list(val) -> Optional[list]:
    parsed = parse_json(val)
    if not isinstance(parsed, list):
        return None
    seen = set()
    result = []
    for item in parsed:
        if not item:
            continue
        normalized = str(item).strip().title()
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result or None


def clean_brochure(val) -> Optional[str]:
    if not val or not isinstance(val, str):
        return None
    if val.strip().lower() in ("null", "none", ""):
        return None
    return val.strip()


def clean_year(val) -> Optional[int]:
    if not val or val == 0:
        return None
    return val


def clean_battery_capacity(val) -> Optional[str]:
    if not val:
        return None
    cleaned = str(val).strip()
    if not cleaned or cleaned.lower() in ("null", "none"):
        return None
    if "kwh" in cleaned.lower():
        return cleaned
    return f"{cleaned} kWh"


def clean_weight(val) -> Optional[str]:
    if not val:
        return None
    cleaned = str(val).strip()
    if not cleaned:
        return None
    if "kg" in cleaned.lower():
        return cleaned
    return f"{cleaned} kg"


def normalize_text(val) -> Optional[str]:
    if not val or not isinstance(val, str):
        return None
    return val.strip().title() or None


BODYSTYLE_MAP = {
    "sport utilities": "SUV",
    "sport utilitie":  "SUV",
    "suv":             "SUV",
    "muv":             "MUV",
    "hatchback":       "Hatchback",
    "sedan":           "Sedan",
    "coupe":           "Coupe",
    "convertible":     "Convertible",
    "pickup":          "Pickup Truck",
    "van":             "Van",
    "minivan":         "Minivan",
}


def clean_bodystyle(val) -> Optional[str]:
    if not val or not isinstance(val, str):
        return None
    return BODYSTYLE_MAP.get(val.strip().lower(), val.strip().title())


HTML_FIELDS_CAR = {
    "overview", "latest_updates", "engine_and_performance",
    "interior", "exterior", "safety", "competition",
    "key_highlights", "final_verdict", "buying_advice",
    "fuel_economy", "pricing_and_features", "city_overview",
    "city_content", "overall", "whats_new",
}

LIST_FIELDS_CAR = {
    "seat_capacities", "transmissions", "fuel_types",
}


def clean_car(car: dict) -> dict:
    for field in HTML_FIELDS_CAR:
        if field in car:
            car[field] = strip_html(car[field])

    for field in LIST_FIELDS_CAR:
        if field in car:
            car[field] = clean_list(car[field])

    if "faq_data" in car:
        car["faq_data"] = parse_json(car["faq_data"])

    for field in ("pros", "cons"):
        if field in car:
            parsed = parse_json(car[field])
            car[field] = parsed if isinstance(parsed, list) else strip_html(car[field])

    car["brochure"] = clean_brochure(car.get("brochure"))
    car["year"]     = clean_year(car.get("year"))

    return car


def clean_trim(trim: dict) -> dict:
    trim["battery_capacity"] = clean_battery_capacity(trim.get("battery_capacity"))
    trim["kerb_weight"]      = clean_weight(trim.get("kerb_weight"))
    trim["gross_weight"]     = clean_weight(trim.get("gross_weight"))
    trim["bodystyle"]        = clean_bodystyle(trim.get("bodystyle"))
    trim["transmission"]     = normalize_text(trim.get("transmission"))

    if "additional_features" in trim:
        trim["additional_features"] = strip_html(trim["additional_features"])

    if "tags" in trim:
        trim["tags"] = parse_json(trim["tags"])

    return trim


def clean_news(news: dict) -> dict:
    for field in ("excerpt", "description"):
        if field in news:
            news[field] = strip_html(news[field])
    return news


def clean_comparison(comp: dict) -> dict:
    for field in ("description", "content", "car1_summary", "car2_summary",
                  "car1_why_choose", "car2_why_choose",
                  "car1_recommendation", "car2_recommendation"):
        if field in comp:
            comp[field] = strip_html(comp[field])
    return comp


def clean_content_fields(payload: dict) -> dict:
    if "car" in payload:
        payload["car"] = clean_car(payload["car"])

    payload["trims"]        = [clean_trim(t) for t in payload.get("trims", [])]
    payload["related_news"] = [clean_news(n) for n in payload.get("related_news", [])]
    payload["comparisons"]  = [clean_comparison(c) for c in payload.get("comparisons", [])]

    return payload