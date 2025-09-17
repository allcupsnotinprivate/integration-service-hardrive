from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app import exceptions


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(exceptions.ServiceError)
    async def base_service_error_handler(request: Request, exc: exceptions.ServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "ServiceError", "message": str(exc)},
        )

    @app.exception_handler(exceptions.NotFoundError)
    async def not_found_error_handler(request: Request, exc: exceptions.NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": "NotFoundError", "message": str(exc)},
        )

    @app.exception_handler(exceptions.DataError)
    async def data_error_handler(request: Request, exc: exceptions.DataError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "DataError", "message": str(exc)},
        )

    @app.exception_handler(exceptions.DuplicateError)
    async def duplication_error_handler(request: Request, exc: exceptions.DuplicateError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "DuplicateError", "message": str(exc)},
        )

    @app.exception_handler(exceptions.ValidationError)
    async def validation_error_handler(request: Request, exc: exceptions.ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": "ValidationError", "message": str(exc)},
        )

    @app.exception_handler(exceptions.PermissionDeniedError)
    async def permission_denied_error_handler(
        request: Request, exc: exceptions.OperationNotAllowedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": "PermissionDeniedError", "message": str(exc)},
        )

    @app.exception_handler(exceptions.UnauthorizedError)
    async def unauthorized_error_handler(request: Request, exc: exceptions.UnauthorizedError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"error": "UnauthorizedError", "message": str(exc)},
        )
