from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config.settings import settings
from src.logger.logger_service import logger_service, SQLAlchemyHandler
import logging

DATABASE_URL = (
    f"mysql+pymysql://"
    f"{settings.DB_USERNAME}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:"
    f"{settings.DB_PORT}/"
    f"{settings.DB_DATABASE}"
)

is_dev = settings.APP_ENV == "development"

engine = create_engine(
    DATABASE_URL,
    pool_size=5 if is_dev else 30,
    max_overflow=0,
    pool_timeout=60,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

if is_dev:
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.handlers = [SQLAlchemyHandler()]
    sqlalchemy_logger.setLevel(logging.INFO)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger_service.log(
            "Database connected successfully",
            "Database",
        )

    except Exception as error:
        logger_service.error(
            "Database connection failed",
            str(error),
            "Database",
        )
        raise