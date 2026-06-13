from fastapi import APIRouter
from src.routes.car_router import car_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(car_router)