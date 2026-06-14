from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.database.sql_connection import db_connection
from src.database.qdrant_connection import qdrant_connection
from src.logger.logger_service import logger_service
from src.error.global_exception_handler import global_exception_handler
from src.routes.index import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_connection()
    qdrant_connection()

    yield

app = FastAPI(
    title="CarHP RAG API",
    lifespan=lifespan,
)

logger_service.log("Application logger initialized", "Main")

app.include_router(api_router)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)