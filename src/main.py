from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.database.connection import db_connection
from src.logger.logger_service import logger_service
from src.error.global_exception_handler import global_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    db_connection()

    yield

app = FastAPI(
    title="CarHP RAG API",
    lifespan=lifespan,
)

logger_service.log("Application logger initialized", "Main")

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)