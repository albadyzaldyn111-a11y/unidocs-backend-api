"""
Unified error response contract:
{ "success": false, "message": "...", "code": "ERROR_CODE" }
Never leak stack traces to the client; log them server-side instead.
"""
import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("unidocs")


class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        self.status_code = status_code


def _error_body(message: str, code: str) -> dict:
    return {"success": False, "message": message, "code": code}


async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=_error_body(exc.message, exc.code))


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=_error_body(str(exc.detail), "HTTP_ERROR"))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=_error_body("Invalid request data", "VALIDATION_ERROR"))


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content=_error_body("Internal server error", "INTERNAL_ERROR"))
