import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        # A field_validator that raises carries the exception object in ctx, which the
        # plain JSON encoder refuses: that turned a 422 into a 500.
        encoded = jsonable_encoder(exc.errors())
        return JSONResponse(status_code=422, content={"error": "validation_error", "detail": encoded})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": "http_error", "detail": exc.detail})

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        # str(exc) can carry connection strings, SQL fragments and file paths — keep it server-side only.
        logger.exception("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "detail": "An unexpected error occurred."},
        )