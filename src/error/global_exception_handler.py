import traceback
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.settings import settings
from src.logger.logger_service import logger_service


async def global_exception_handler(
    request: Request,
    exception: Exception,
):
    status_code = (
        exception.status_code
        if isinstance(exception, StarletteHTTPException)
        else 500
    )

    if isinstance(exception, StarletteHTTPException):
        error_response = exception.detail
    else:
        if settings.APP_ENV != "prod":
            error_response = {
                "message": str(exception),
                "stack": traceback.format_exc(),
            }
        else:
            error_response = "Internal server error"

    logger_service.error(
        f"Unhandled Exception in {settings.APP_NAME}",
        str(error_response),
        "GlobalExceptionHandler",
    )

    message = (
        error_response
        if isinstance(error_response, str)
        else error_response.get("message", error_response)
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "statusCode": status_code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )