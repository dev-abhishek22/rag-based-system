from typing import Optional, Any


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _fmt_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if not _is_empty(v))
    if isinstance(value, dict):
        return "; ".join(f"{k}: {v}" for k, v in value.items() if not _is_empty(v))
    return str(value)


def _add_field(parts: list[str], data: dict, field: str, label: str):
    val = data.get(field)
    if not _is_empty(val):
        parts.append(f"{label}: {_fmt_value(val)}")


def _chunk(text: str, chunk_type: str, metadata: dict) -> Optional[dict]:
    text = text.strip()
    if not text:
        return None

    return {
        "text": text,
        "metadata": {
            **{k: v for k, v in metadata.items() if not _is_empty(v)},
            "chunk_type": chunk_type,
        },
    }


def _base_metadata(car: dict) -> dict:
    return {
        "car_id": car.get("car_id"),
        "car_name": car.get("car_name"),
        "brand_id": car.get("brand_id"),
        "brand_name": car.get("brand_name"),
        "brand_slug": car.get("brand_slug"),
        "model_id": car.get("model_id"),
        "model_name": car.get("model_name"),
        "model_slug": car.get("model_slug"),
        "submodel_id": car.get("submodel_id"),
        "submodel_name": car.get("submodel_name"),
        "submodel_slug": car.get("submodel_slug"),
        "url": car.get("url"),
        "is_ev": car.get("is_ev"),
        "is_popular": car.get("is_popular"),
        "is_trending": car.get("is_trending"),
        "is_best_sell": car.get("is_best_sell"),
        "is_upcoming": car.get("is_upcoming"),
        "is_discontinued": car.get("is_discontinued"),
        "is_gst_reform": car.get("is_gst_reform"),
        "min_price": car.get("min_price"),
        "max_price": car.get("max_price"),
        "min_mileage": car.get("min_mileage"),
        "max_mileage": car.get("max_mileage"),
        "min_engine_displacement": car.get("min_engine_displacement"),
        "max_engine_displacement": car.get("max_engine_displacement"),
        "min_no_of_airbags": car.get("min_no_of_airbags"),
        "max_no_of_airbags": car.get("max_no_of_airbags"),
        "overall_rating": car.get("overall_rating"),
        "year": car.get("year"),
        "launched_at": car.get("launched_at"),
        "discontinued_at": car.get("discontinued_at"),
        "upcoming_date": car.get("upcoming_date"),
        "upcoming_type": car.get("upcoming_type"),
        "new_car_id": car.get("new_car_id"),
    }


def _chunk_car_overview(car: dict, meta: dict) -> Optional[dict]:
    parts = []

    _add_field(parts, car, "car_name", "Car")
    _add_field(parts, car, "brand_name", "Brand")
    _add_field(parts, car, "model_name", "Model")
    _add_field(parts, car, "submodel_name", "Submodel")
    _add_field(parts, car, "description", "Description")
    _add_field(parts, car, "overview", "Overview")
    _add_field(parts, car, "latest_updates", "Latest updates")
    _add_field(parts, car, "whats_new", "What's new")
    _add_field(parts, car, "launched_at", "Launched at")
    _add_field(parts, car, "upcoming_date", "Upcoming date")
    _add_field(parts, car, "upcoming_type", "Upcoming type")
    _add_field(parts, car, "overall_rating", "Overall rating")

    return _chunk("\n".join(parts), "car_overview", meta)


def _chunk_car_price_summary(car: dict, meta: dict) -> Optional[dict]:
    parts = [f"Price and basic summary for {car.get('car_name', 'this car')}"]

    for field, label in [
        ("min_price", "Minimum price"),
        ("max_price", "Maximum price"),
        ("gst_reform_price", "GST reform price"),
        ("latest_offers", "Latest offers"),
        ("pricing_and_features", "Pricing and features"),
        ("min_mileage", "Minimum mileage"),
        ("max_mileage", "Maximum mileage"),
        ("min_engine_displacement", "Minimum engine displacement"),
        ("max_engine_displacement", "Maximum engine displacement"),
        ("min_no_of_airbags", "Minimum airbags"),
        ("max_no_of_airbags", "Maximum airbags"),
        ("fuel_types", "Fuel types"),
        ("transmissions", "Transmissions"),
        ("seat_capacities", "Seat capacities"),
    ]:
        _add_field(parts, car, field, label)

    return _chunk("\n".join(parts), "car_price_summary", meta)


def _chunk_car_editorial(car: dict, meta: dict) -> list[dict]:
    chunks = []

    sections = [
        ("engine_and_performance", "Engine and performance", "car_engine_performance"),
        ("interior", "Interior", "car_interior"),
        ("exterior", "Exterior", "car_exterior"),
        ("safety", "Safety", "car_safety"),
        ("competition", "Competition", "car_competition"),
        ("fuel_economy", "Fuel economy", "car_fuel_economy"),
        ("buying_advice", "Buying advice", "car_buying_advice"),
        ("final_verdict", "Final verdict", "car_final_verdict"),
        ("overall", "Overall review", "car_overall_review"),
        ("city_overview", "City overview", "car_city_overview"),
        ("city_content", "City content", "car_city_content"),
        ("upcoming_updates", "Upcoming updates", "car_upcoming_updates"),
    ]

    for field, label, chunk_type in sections:
        if not _is_empty(car.get(field)):
            chunk = _chunk(f"{label} for {car.get('car_name')}:\n{car[field]}", chunk_type, meta)
            if chunk:
                chunks.append(chunk)

    return chunks


def _chunk_car_pros_cons(car: dict, meta: dict) -> Optional[dict]:
    parts = []

    _add_field(parts, car, "key_highlights", "Key highlights")

    if car.get("pros"):
        parts.append("Pros:")
        parts.extend(f"+ {p}" for p in car["pros"])

    if car.get("cons"):
        parts.append("Cons:")
        parts.extend(f"- {c}" for c in car["cons"])

    return _chunk("\n".join(parts), "car_pros_cons", meta)


def _chunk_faqs(car: dict, meta: dict) -> list[dict]:
    chunks = []
    faqs = car.get("faq_data")

    if not isinstance(faqs, list):
        return chunks

    for idx, item in enumerate(faqs, start=1):
        q = str(item.get("question", "")).strip()
        a = str(item.get("answer", "")).strip()

        if not q or not a:
            continue

        chunk = _chunk(
            f"Question: {q}\nAnswer: {a}",
            "car_faq",
            {
                **meta,
                "faq_index": idx,
                "question": q,
            },
        )

        if chunk:
            chunks.append(chunk)

    return chunks


TRIM_SECTIONS = {
    "trim_engine_performance": [
        ("trim_name", "Variant"),
        ("price", "Price"),
        ("fuel_type", "Fuel type"),
        ("engine", "Engine"),
        ("engine_type", "Engine type"),
        ("configuration", "Configuration"),
        ("displacement", "Displacement"),
        ("power", "Power"),
        ("torque", "Torque"),
        ("max_power", "Max power"),
        ("max_torque", "Max torque"),
        ("transmission", "Transmission"),
        ("transmission_type", "Transmission type"),
        ("gearbox", "Gearbox"),
        ("drive_type", "Drive type"),
        ("top_speed", "Top speed"),
        ("acceleration", "Acceleration"),
        ("acceleration_0_100kmph", "0-100 kmph acceleration"),
        ("mileage", "Mileage"),
        ("fuel_tank", "Fuel tank"),
        ("drive_modes", "Drive modes"),
        ("paddle_shifters", "Paddle shifters"),
    ],
    "trim_ev_hybrid": [
        ("trim_name", "Variant"),
        ("battery_capacity", "Battery capacity"),
        ("battery_type", "Battery type"),
        ("battery_saver", "Battery saver"),
        ("motor_type", "Motor type"),
        ("motor_power", "Motor power"),
        ("max_range", "Max range"),
        ("range_tested", "Tested range"),
        ("electric_mileage_arai", "Electric mileage ARAI"),
        ("wltp_mileage", "WLTP mileage"),
        ("charging_port", "Charging port"),
        ("charging_options", "Charging options"),
        ("charger_type", "Charger type"),
        ("fast_charging", "Fast charging"),
        ("charging_time", "Charging time"),
        ("charging_time_a_c", "AC charging time"),
        ("charging_time_d_c", "DC charging time"),
        ("regenerative_braking", "Regenerative braking"),
        ("regenerative_braking_levels", "Regenerative braking levels"),
        ("vehicle_to_vehicle_charging", "Vehicle to vehicle charging"),
        ("vehicle_to_load_charging", "Vehicle to load charging"),
        ("hybrid_type", "Hybrid type"),
        ("secondary_fuel_type", "Secondary fuel type"),
    ],
    "trim_dimensions": [
        ("trim_name", "Variant"),
        ("body_type", "Body type"),
        ("bodystyle", "Body style"),
        ("length", "Length"),
        ("width", "Width"),
        ("height", "Height"),
        ("wheelbase", "Wheelbase"),
        ("ground_clearance", "Ground clearance"),
        ("ground_clearance_laden", "Ground clearance laden"),
        ("ground_clearance_unladen", "Ground clearance unladen"),
        ("kerb_weight", "Kerb weight"),
        ("gross_weight", "Gross weight"),
        ("seating_capacity", "Seating capacity"),
        ("no_of_doors", "Doors"),
        ("boot_space", "Boot space"),
        ("boot_space_rear_seat_folding", "Boot space rear seat folding"),
        ("approach_angle", "Approach angle"),
        ("break_over_angle", "Break over angle"),
        ("departure_angle", "Departure angle"),
        ("drag_coefficient", "Drag coefficient"),
    ],
    "trim_wheels_suspension": [
        ("trim_name", "Variant"),
        ("tyre_size", "Tyre size"),
        ("tyre_type", "Tyre type"),
        ("wheel_size", "Wheel size"),
        ("alloy_wheels", "Alloy wheels"),
        ("wheel_covers", "Wheel covers"),
        ("alloy_wheel_size", "Alloy wheel size"),
        ("front_track", "Front track"),
        ("rear_track", "Rear track"),
        ("turning_radius", "Turning radius"),
        ("front_suspension", "Front suspension"),
        ("rear_suspension", "Rear suspension"),
        ("front_brake_type", "Front brake"),
        ("rear_brake_type", "Rear brake"),
        ("steering_type", "Steering type"),
        ("steering_column", "Steering column"),
        ("steering_gear_type", "Steering gear type"),
        ("shock_absorbers_type", "Shock absorbers type"),
    ],
    "trim_safety": [
        ("trim_name", "Variant"),
        ("no_of_airbags", "Airbags"),
        ("driver_airbag", "Driver airbag"),
        ("passenger_airbag", "Passenger airbag"),
        ("side_airbag", "Side airbag"),
        ("side_airbag_rear", "Rear side airbag"),
        ("curtain_airbag", "Curtain airbag"),
        ("anti_lock_braking_system_abs", "ABS"),
        ("electronic_brakeforce_distribution_ebd", "EBD"),
        ("electronic_stability_control_esc", "ESC"),
        ("brake_assist", "Brake assist"),
        ("hill_assist", "Hill assist"),
        ("hill_descent_control", "Hill descent control"),
        ("tyre_pressure_monitoring_system_tpms", "TPMS"),
        ("360_view_camera", "360 view camera"),
        ("rear_camera", "Rear camera"),
        ("parking_sensors", "Parking sensors"),
        ("isofix_child_seat_mounts", "ISOFIX child seat mounts"),
        ("child_safety_locks", "Child safety locks"),
        ("seat_belt_warning", "Seat belt warning"),
        ("door_ajar_warning", "Door ajar warning"),
        ("engine_immobilizer", "Engine immobilizer"),
        ("anti_theft_alarm", "Anti theft alarm"),
        ("speed_alert", "Speed alert"),
        ("speed_sensing_auto_door_lock", "Speed sensing auto door lock"),
        ("global_ncap_safety_rating", "Global NCAP safety rating"),
        ("bharat_ncap_safety_rating", "Bharat NCAP safety rating"),
    ],
    "trim_comfort": [
        ("trim_name", "Variant"),
        ("air_conditioner", "Air conditioner"),
        ("heater", "Heater"),
        ("automatic_climate_control", "Automatic climate control"),
        ("rear_ac_vents", "Rear AC vents"),
        ("power_steering", "Power steering"),
        ("adjustable_steering", "Adjustable steering"),
        ("height_adjustable_driver_seat", "Height adjustable driver seat"),
        ("electric_adjustable_seats", "Electric adjustable seats"),
        ("ventilated_seats", "Ventilated seats"),
        ("heated_seats", "Heated seats"),
        ("leather_seats", "Leather seats"),
        ("cruise_control", "Cruise control"),
        ("keyless_entry", "Keyless entry"),
        ("power_windows", "Power windows"),
        ("foldable_rear_seat", "Foldable rear seat"),
        ("cooled_glovebox", "Cooled glovebox"),
        ("remote_trunk_opener", "Remote trunk opener"),
        ("power_boot", "Power boot"),
        ("rain_sensing_wiper", "Rain sensing wiper"),
        ("start_stop", "Start stop"),
        ("idle_start_stop_system", "Idle start stop system"),
    ],
    "trim_infotainment": [
        ("trim_name", "Variant"),
        ("touchscreen", "Touchscreen"),
        ("touchscreen_size", "Touchscreen size"),
        ("android_auto", "Android Auto"),
        ("apple_carplay", "Apple CarPlay"),
        ("wireless_phone_charging", "Wireless phone charging"),
        ("wireless_charging", "Wireless charging"),
        ("bluetooth_connectivity", "Bluetooth connectivity"),
        ("navigation_system", "Navigation system"),
        ("navigation_with_live_traffic", "Navigation with live traffic"),
        ("radio", "Radio"),
        ("usb_charger", "USB charger"),
        ("usb_ports", "USB ports"),
        ("speakers", "Speakers"),
        ("no_of_speakers", "Number of speakers"),
        ("voice_commands", "Voice commands"),
        ("google_alexa_connectivity", "Google Alexa connectivity"),
        ("smartwatch_app", "Smartwatch app"),
        ("over_the_air_ota_updates", "OTA updates"),
        ("live_location", "Live location"),
        ("digital_cluster", "Digital cluster"),
        ("digital_cluster_size", "Digital cluster size"),
    ],
    "trim_interior_exterior": [
        ("trim_name", "Variant"),
        ("upholstery", "Upholstery"),
        ("fabric_upholstery", "Fabric upholstery"),
        ("leather_wrapped_steering_wheel", "Leather wrapped steering wheel"),
        ("dual_tone_dashboard", "Dual tone dashboard"),
        ("ambient_light_colour_numbers", "Ambient light colours"),
        ("additional_features", "Additional features"),
        ("sunroof", "Sunroof"),
        ("roof_rails", "Roof rails"),
        ("fog_lights", "Fog lights"),
        ("led_headlamps", "LED headlamps"),
        ("led_drls", "LED DRLs"),
        ("led_taillights", "LED taillights"),
        ("led_fog_lamps", "LED fog lamps"),
        ("halogen_headlamps", "Halogen headlamps"),
        ("projector_headlamps", "Projector headlamps"),
        ("rear_window_wiper", "Rear window wiper"),
        ("rear_window_washer", "Rear window washer"),
        ("rear_window_defogger", "Rear window defogger"),
        ("rear_spoiler", "Rear spoiler"),
        ("outside_rear_view_mirror_orvm", "ORVM"),
        ("chrome_grille", "Chrome grille"),
        ("tinted_glass", "Tinted glass"),
        ("puddle_lamps", "Puddle lamps"),
        ("dual_tone_body_colour", "Dual tone body colour"),
    ],
    "trim_ownership": [
        ("trim_name", "Variant"),
        ("warranty_years", "Warranty years"),
        ("warranty_kilometres", "Warranty kilometres"),
        ("battery_warranty", "Battery warranty"),
        ("battery_warranty_years", "Battery warranty years"),
        ("battery_warranty_kilometres", "Battery warranty kilometres"),
        ("service_cost", "Service cost"),
    ],
}


def _trim_metadata(trim: dict, meta: dict) -> dict:
    return {
        **meta,
        "trim_id": trim.get("trim_id"),
        "trim_name": trim.get("trim_name"),
        "absolute_price": trim.get("absolute_price"),
        "is_base": trim.get("is_base"),
        "is_top": trim.get("is_top"),
        "is_new": trim.get("is_new"),
        "is_popular": trim.get("is_popular"),
        "is_discontinued": trim.get("is_discontinued"),
        "fuel_type": trim.get("fuel_type"),
        "price": trim.get("absolute_price"),
        "launched_at": trim.get("launched_at"),
        "discontinued_at": trim.get("discontinued_at"),
        "trim_active_date": trim.get("trim_active_date"),
        "trim_discon_date": trim.get("trim_discon_date"),
    }


def _chunk_trim_sections(trim: dict, meta: dict) -> list[dict]:
    chunks = []
    trim_meta = _trim_metadata(trim, meta)

    for chunk_type, fields in TRIM_SECTIONS.items():
        parts = []

        for field, label in fields:
            _add_field(parts, trim, field, label)

        chunk = _chunk("\n".join(parts), chunk_type, trim_meta)
        if chunk:
            chunks.append(chunk)

    return chunks


def _chunk_city_prices(prices: list, trim_map: dict, meta: dict, batch_size: int = 25) -> list[dict]:
    chunks = []
    prices_by_trim = {}

    for p in prices:
        trim_id = p.get("trim_id")
        prices_by_trim.setdefault(trim_id, []).append(p)

    for trim_id, rows in prices_by_trim.items():
        trim_name = trim_map.get(trim_id, str(trim_id))

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            parts = [f"City prices for {meta.get('car_name')} {trim_name}:"]

            for p in batch:
                line = []
                _add_field(line, p, "city_name", "City")
                _add_field(line, p, "ex_showroom_price", "Ex-showroom price")
                _add_field(line, p, "on_road_price", "On-road price")
                _add_field(line, p, "rto", "RTO")
                _add_field(line, p, "insurance", "Insurance")
                _add_field(line, p, "others", "Others")
                _add_field(line, p, "optional_accessories", "Optional accessories")
                parts.append(" | ".join(line))

            chunk = _chunk(
                "\n".join(parts),
                "trim_city_prices",
                {
                    **meta,
                    "trim_id": trim_id,
                    "trim_name": trim_name,
                    "city_price_batch": i // batch_size + 1,
                },
            )

            if chunk:
                chunks.append(chunk)

    return chunks


def _chunk_comparisons(comparisons: list, meta: dict) -> list[dict]:
    chunks = []

    for c in comparisons:
        parts = []

        for field, label in [
            ("title", "Title"),
            ("car_name", "Car"),
            ("compare_car_name", "Compared with"),
            ("brand_name", "Brand"),
            ("compare_brand_name", "Compared brand"),
            ("description", "Description"),
            ("content", "Content"),
            ("car1_summary", "Car 1 summary"),
            ("car2_summary", "Car 2 summary"),
            ("car1_why_choose", "Why choose car 1"),
            ("car2_why_choose", "Why choose car 2"),
            ("car1_recommendation", "Car 1 recommendation"),
            ("car2_recommendation", "Car 2 recommendation"),
        ]:
            _add_field(parts, c, field, label)

        chunk = _chunk(
            "\n".join(parts),
            "car_comparison",
            {
                **meta,
                "compare_car_id": c.get("compare_car_id"),
                "compare_car_name": c.get("compare_car_name"),
                "compare_brand_name": c.get("compare_brand_name"),
                "is_popular": c.get("is_popular"),
                "car_url": c.get("car_url"),
                "compare_car_url": c.get("compare_car_url"),
            },
        )

        if chunk:
            chunks.append(chunk)

    return chunks


def _chunk_similar_cars(similar_cars: list, meta: dict) -> Optional[dict]:
    parts = [f"Similar cars for {meta.get('car_name')}:"]

    for car in similar_cars:
        line = []
        _add_field(line, car, "similar_car_name", "Car")
        _add_field(line, car, "brand_name", "Brand")
        _add_field(line, car, "model_name", "Model")
        _add_field(line, car, "submodel_name", "Submodel")
        _add_field(line, car, "overall_rating", "Rating")
        _add_field(line, car, "is_ev", "EV")
        _add_field(line, car, "is_discontinued", "Discontinued")

        if line:
            parts.append(" | ".join(line))

    return _chunk("\n".join(parts), "similar_cars", meta)


def _chunk_news(news_list: list, meta: dict) -> list[dict]:
    chunks = []

    for news in news_list:
        parts = []
        _add_field(parts, news, "title", "Title")
        _add_field(parts, news, "excerpt", "Excerpt")

        chunk = _chunk(
            "\n".join(parts),
            "related_news",
            {
                **meta,
                "news_flag": news.get("news_flag"),
                "news_url": news.get("url"),
                "updated_at": news.get("updated_at"),
            },
        )

        if chunk:
            chunks.append(chunk)

    return chunks


def _chunk_standout_features(features: list, meta: dict) -> Optional[dict]:
    parts = [f"Standout features of {meta.get('car_name')}:"]

    for feature in features:
        _add_field(parts, feature, "caption", "Feature")

    return _chunk("\n".join(parts), "standout_features", meta)


def _image_metadata(images: list, meta: dict) -> list[dict]:
    docs = []

    for img in images:
        docs.append({
            "text": "",
            "metadata": {
                **meta,
                "chunk_type": "image_metadata",
                "image_id": img.get("id"),
                "image_path": img.get("image_path"),
                "alt_text": img.get("alt_text"),
                "image_type": img.get("image_type"),
                "color_id": img.get("color_id"),
                "color_name": img.get("color_name"),
                "color_code": img.get("color_code"),
            },
        })

    return docs


def format_car_chunks(payload: dict, include_images: bool = False) -> list[dict]:
    car = payload.get("car", {})
    trims = payload.get("trims", [])
    prices = payload.get("trim_city_prices", [])
    comparisons = payload.get("comparisons", [])
    similar_cars = payload.get("similar_cars", [])
    news = payload.get("related_news", [])
    standout = payload.get("standout_features", [])
    images = payload.get("images", [])

    meta = _base_metadata(car)

    trim_map = {
        t.get("trim_id"): t.get("trim_name", "")
        for t in trims
        if t.get("trim_id")
    }

    chunks = []

    for chunk in [
        _chunk_car_overview(car, meta),
        _chunk_car_price_summary(car, meta),
        _chunk_car_pros_cons(car, meta),
        _chunk_similar_cars(similar_cars, meta),
        _chunk_standout_features(standout, meta),
    ]:
        if chunk:
            chunks.append(chunk)

    chunks.extend(_chunk_car_editorial(car, meta))
    chunks.extend(_chunk_faqs(car, meta))

    for trim in trims:
        chunks.extend(_chunk_trim_sections(trim, meta))

    chunks.extend(_chunk_city_prices(prices, trim_map, meta))
    chunks.extend(_chunk_comparisons(comparisons, meta))
    chunks.extend(_chunk_news(news, meta))

    if include_images:
        chunks.extend(_image_metadata(images, meta))

    return chunks