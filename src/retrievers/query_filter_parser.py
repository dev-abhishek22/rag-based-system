import re


def infer_filters_from_query(query: str) -> dict:
    q = query.lower()
    filters = {}

    brands = {
        "tata": "Tata",
        "mahindra": "Mahindra",
        "hyundai": "Hyundai",
        "kia": "Kia",
        "maruti": "Maruti Suzuki",
        "maruti suzuki": "Maruti Suzuki",
        "toyota": "Toyota",
        "honda": "Honda",
        "renault": "Renault",
        "skoda": "Skoda",
        "volkswagen": "Volkswagen",
    }

    for keyword, brand_name in brands.items():
        if keyword in q:
            filters["brand_name"] = brand_name
            break

    if "suv" in q or "suvs" in q:
        filters["submodel_name"] = "SUV"

    if "sedan" in q or "sedans" in q:
        filters["submodel_name"] = "Sedan"

    if "hatchback" in q or "hatchbacks" in q:
        filters["submodel_name"] = "Hatchback"

    if "ev" in q or "electric" in q:
        filters["fuel_type"] = "Electric"

    if "petrol" in q:
        filters["fuel_type"] = "Petrol"

    if "diesel" in q:
        filters["fuel_type"] = "Diesel"

    if any(word in q for word in ["safe", "safety", "safest", "rating"]):
        filters["chunk_types"] = ["car_safety", "car_overview"]

    elif any(word in q for word in ["price", "under", "budget", "lakh"]):
        filters["chunk_types"] = ["car_price", "car_overview", "car_trim"]

    elif any(word in q for word in ["compare", "comparison", "versus", "vs"]):
        filters["chunk_types"] = ["car_comparison", "car_overview"]

    elif any(word in q for word in ["feature", "features", "sunroof", "adas", "airbags"]):
        filters["chunk_types"] = ["car_feature", "car_safety", "car_overview"]

    else:
        filters["chunk_types"] = [
            "car_overview",
            "car_safety",
            "car_feature",
            "car_price",
            "car_trim",
        ]

    match = re.search(r"under\s*[₹rs\.]*\s*(\d+)\s*lakh", q)

    if match:
        filters["max_price"] = int(match.group(1)) * 100000

    return filters