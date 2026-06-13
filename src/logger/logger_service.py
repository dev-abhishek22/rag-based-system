from pathlib import Path
import sys
from loguru import logger
from typing import Optional
import logging

class SQLAlchemyHandler(logging.Handler):
    def emit(self, record):
        logger.bind(context="SQL").debug(record.getMessage())

class LoggerService:
    def __init__(self):
        Path("logs/api").mkdir(parents=True, exist_ok=True)
           
        logger.remove()

        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[context]: <15}</cyan> | "
            "<level>{message}</level>"
        )

        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level} | "
            "{extra[context]} | "
            "{message}"
        )

        logger.add(
            sys.stdout,
            level="DEBUG",
            colorize=True,
            format=console_format,
        )

        logger.add(
            "logs/info-{time:YYYY-MM-DD}.log",
            level="INFO",
            format=file_format,
            rotation="20 MB",
            retention="3 days",
            compression="zip",
        )

        logger.add(
            "logs/error-{time:YYYY-MM-DD}.log",
            level="ERROR",
            format=file_format,
            rotation="20 MB",
            retention="3 days",
            compression="zip",
        )

        logger.add(
            "logs/api/{time:YYYY-MM-DD}-api.log",
            level="INFO",
            format=file_format,
            rotation="20 MB",
            retention="3 days",
            compression="zip",
            filter=lambda record: record["extra"].get("context") == "API",
        )

        self.logger = logger.bind(context="APP")
        self.api_logger = logger.bind(context="API")

    def log(self, message: str, context: str = "APP"):
        self.logger.bind(context=context).info(message)

    def error(
        self,
        message: str,
        trace: Optional[str] = None,
        context: str = "APP",
    ):
        full_message = f"{message} | Trace: {trace}" if trace else message
        self.logger.bind(context=context).error(full_message)

    def warn(self, message: str, context: str = "APP"):
        self.logger.bind(context=context).warning(message)

    def debug(self, message: str, context: str = "APP"):
        self.logger.bind(context=context).debug(message)

    def log_api_request(self, message: str):
        self.api_logger.info(message)


logger_service = LoggerService()