"""Global API error handlers — consistent JSON responses."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_body(
    message: str,
    *,
    code: str = "error",
    detail: str | None = None,
    status_code: int = 500,
) -> dict:
    return {
        "error": True,
        "code": code,
        "message": message,
        "detail": detail or message,
        "status_code": status_code,
    }


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        body = {**_error_body(str(detail.get("message", detail)), code="http_error", status_code=exc.status_code), **detail}
    else:
        body = _error_body(str(detail), code="http_error", status_code=exc.status_code)
    return JSONResponse(status_code=exc.status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content=_error_body(
            "Request validation failed",
            code="validation_error",
            detail=str(exc.errors()),
            status_code=422,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "Internal server error",
            code="internal_error",
            detail=str(exc) if str(exc) else None,
            status_code=500,
        ),
    )
