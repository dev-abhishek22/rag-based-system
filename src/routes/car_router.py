from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.sql_connection import get_db
from src.services.car_etl_service import CarEtlService

car_router = APIRouter(prefix="/car", tags=["Car"])


@car_router.get("/{car_id}")
def get_car(car_id: int, db: Session = Depends(get_db)):
    service = CarEtlService()
    payload = service.fetch_single_car_payload(db, car_id)

    return {
        "success": True,
        "data": payload,
    }