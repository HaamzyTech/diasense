import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.time import to_iso8601, utc_now
from app.metrics.prometheus import (
    BACKEND_API_EXCEPTIONS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
    metrics_response,
)

settings = get_settings()
configure_logging()
logger = logging.getLogger("backend-api")

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    started_at = perf_counter()
    response = await call_next(request)
    duration_seconds = perf_counter() - started_at
    response.headers["x-request-id"] = request_id

    HTTP_REQUESTS_TOTAL.labels(request.method, request.url.path, str(response.status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(request.method, request.url.path).observe(duration_seconds)
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
        },
    )
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    BACKEND_API_EXCEPTIONS_TOTAL.labels(exception_type=exc.code).inc()
    logger.warning(
        "app_error",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.code,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    BACKEND_API_EXCEPTIONS_TOTAL.labels(exception_type="request_validation_error").inc()
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "error_code": "request_validation_error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    BACKEND_API_EXCEPTIONS_TOTAL.labels(exception_type="database_error").inc()
    logger.exception(
        "database_error",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "status_code": 500,
        },
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database error",
            "error_code": "database_error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    BACKEND_API_EXCEPTIONS_TOTAL.labels(exception_type="internal_server_error").inc()
    logger.exception(
        "unhandled_error",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "status_code": 500,
        },
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "internal_server_error",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.get("/metrics")
async def metrics():
    return metrics_response()


@app.get("/")
async def root() -> dict:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": to_iso8601(utc_now()),
    }
