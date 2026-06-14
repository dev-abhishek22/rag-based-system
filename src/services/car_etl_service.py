from copy import deepcopy
from decimal import Decimal
from typing import Optional

from src.database.sql_connection import SessionLocal
from src.logger.logger_service import logger_service
from src.repositories.car_etl_repository import CarEtlRepository
from src.utils.cleaners import clean_content_fields
from src.utils.helper import deep_clean, fmt_date, first


class CarEtlService:
    def __init__(self):
        self.repository = CarEtlRepository()

    def fetch_single_car_payload(self, db, car_id: int):
        car = self.repository.get_car_main(db, car_id)

        if not car:
            return None

        trims = self.repository.get_car_trims(db, car_id)
        trim_ids = [t["trim_id"] for t in trims if t.get("trim_id")]

        related_news = self.repository.get_related_news(db, car_id)

        for news in related_news:
            news["url"] = self._make_news_url(news)

        comparisons = self.repository.get_comparisons(db, car_id)
        for comparison in comparisons:
            comparison["comparison_url"] = self._ensure_url(comparison.get("comparison_url"))
            comparison["car_url"] = self._ensure_url(comparison.get("car_url"))
            comparison["compare_car_url"] = self._ensure_url(comparison.get("compare_car_url"))

        payload = {
            "car": car,
            "images": self.repository.get_car_images(db, car_id),
            "trims": trims,
            "trim_city_prices": self.repository.get_trim_city_prices(db, trim_ids),
            "standout_features": self.repository.get_standout_features(db, car_id),
            "similar_cars": self.repository.get_similar_cars(db, car_id),
            "related_news": related_news,
            "comparisons": comparisons,
        }

        payload = deep_clean(payload)
        payload = clean_content_fields(payload)
        payload = self._resolve_fields(payload)
        payload = deep_clean(payload)

        return payload

    def fetch_all_active_car_payloads(self, batch_size: int = 50):
        offset = 0
        total_processed = 0

        while True:
            db = SessionLocal()
            try:
                car_ids = self.repository.get_active_car_ids(
                    db=db, limit=batch_size, offset=offset
                )

                if not car_ids:
                    break

                for car_id in car_ids:
                    try:
                        payload = self.fetch_single_car_payload(db, car_id)

                        if not payload:
                            logger_service.warn(f"Skipped car_id={car_id}, no data found", "CarETL")
                            continue

                        total_processed += 1
                        logger_service.log(f"Prepared cleaned payload for car_id={car_id}", "CarETL")

                        yield payload

                    except Exception as error:
                        logger_service.error(f"Failed to prepare payload for car_id={car_id}", str(error), "CarETL")

                offset += batch_size

            finally:
                db.close()

        logger_service.log(f"Completed. Total processed: {total_processed}", "CarETL")

    def _resolve_fuel_tank(self, trim: dict) -> Optional[str]:
        candidates = [
            (trim.get("petrol_fuel_tank_capacity_litres") or trim.get("petrol_fuel_tank_capacity"), "petrol"),
            (trim.get("cng_fuel_tank_capacity"),   "CNG"),
            (trim.get("diesel_fuel_tank_capacity"), "diesel"),
            (trim.get("lpg_fuel_tank_capacity"),    "LPG"),
            (trim.get("fuel_tank_capacity"),         None),
        ]
        parts = [f"{v}L ({l})" if l else f"{v}L" for v, l in candidates if v]
        return ", ".join(parts) or None

    def _resolve_mileage(self, trim: dict) -> Optional[str]:
        parts = []

        petrol_arai = trim.get("petrol_mileage_arai")
        if petrol_arai:
            text = f"petrol {petrol_arai} km/l ARAI"
            extras = [
                f"{v} km/l {label}"
                for v, label in (
                    (trim.get("petrol_mileage_wltp"),    "WLTP"),
                    (trim.get("petrol_highway_mileage"), "highway"),
                    (trim.get("petrol_overall_mileage"), "overall"),
                )
                if v
            ]
            if extras:
                text += ", " + ", ".join(extras)
            parts.append(text)

        cng_arai = trim.get("cng_mileage_arai")
        if cng_arai:
            text = f"CNG {cng_arai} km/kg ARAI"
            if trim.get("cng_highway_mileage"):
                text += f", {trim['cng_highway_mileage']} km/kg highway"
            parts.append(text)

        diesel_arai = trim.get("diesel_mileage_arai")
        if diesel_arai:
            text = f"diesel {diesel_arai} km/l ARAI"
            extras = [
                f"{v} km/l {label}"
                for v, label in (
                    (trim.get("diesel_mileage_wltp"),    "WLTP"),
                    (trim.get("diesel_highway_mileage"), "highway"),
                )
                if v
            ]
            if extras:
                text += ", " + ", ".join(extras)
            parts.append(text)

        if trim.get("lpg_mileage_arai"):
            parts.append(f"LPG {trim['lpg_mileage_arai']} km/l ARAI")

        electric = trim.get("electric_mileage_arai")
        if electric:
            text = f"electric range {electric} km ARAI"
            if trim.get("wltp_mileage"):
                text += f", {trim['wltp_mileage']} km WLTP"
            parts.append(text)

        if trim.get("city_mileage") and not parts:
            parts.append(f"city mileage {trim['city_mileage']}")

        return "; ".join(parts) or None

    def _resolve_trim(self, trim: dict) -> dict:
        item = dict(trim)

        item["power"]     = first(item.get("max_power"), item.get("max_power_short"))
        item["torque"]    = first(item.get("max_torque"), item.get("max_torque_short"))
        item["fuel_tank"] = self._resolve_fuel_tank(item)
        item["mileage"]   = self._resolve_mileage(item)
        item["sunroof"]   = first(item.get("sunroof"), item.get("sun_roof"))
        item["start_stop"]= first(item.get("engine_spec_start_stop_button"), item.get("comfort_engine_start_stop_button"))

        item["trim_active_date"] = fmt_date(item.get("market_active_date"))
        item["trim_discon_date"] = fmt_date(item.get("market_discon_date"))

        for field in ("launched_at", "discontinued_at"):
            if field in item:
                item[field] = fmt_date(item[field])

        for k, v in item.items():
            if isinstance(v, Decimal):
                item[k] = float(v)

        return item

    def _resolve_fields(self, payload: dict) -> dict:
        resolved = deepcopy(payload)
        car = resolved.get("car", {})

        if car.get("new_car_id"):
            car["successor_car_id"] = car["new_car_id"]

        for field in ("launched_at", "discontinued_at", "upcoming_date"):
            if field in car:
                car[field] = fmt_date(car[field])

        resolved["trims"] = [self._resolve_trim(t) for t in resolved.get("trims", [])]

        return resolved
    
    def _ensure_url(self, url):
        if not url:
            return None

        url = str(url).strip()

        if not url.startswith("/"):
            url = f"/{url}"

        return url

    def _make_news_url(self, news: dict):
        url = news.get("url")

        if not url:
            return None

        url = str(url).strip()

        if url.startswith("/car-news/"):
            return url

        if url.startswith("car-news/"):
            return f"/{url}"

        return f"/car-news/{url.lstrip('/')}"
