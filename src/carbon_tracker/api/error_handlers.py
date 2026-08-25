"""Manejo centralizado de errores: un unico lugar define su forma en HTTP."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from carbon_tracker.domain.errors import (
    CarbonTrackerDomainError,
    InvalidTripError,
    UnsupportedVehicleTypeError,
)


def _error_body(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict:
    """Construye el cuerpo uniforme de error del servicio."""
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def _json_error(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Unica via de construccion de respuestas de error HTTP."""
    return JSONResponse(
        status_code=status_code,
        content=_error_body(code, message, details),
    )


def _field_from_location(location: tuple[Any, ...]) -> str:
    """Aplana la ruta del campo reportada por Pydantic (p.ej. ('body', 'x'))."""
    return ".".join(str(part) for part in location if part != "body")


async def _handle_request_validation_error(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Traduce fallos del contrato HTTP (Pydantic) a 422 con forma uniforme."""
    details = [
        {"field": _field_from_location(error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return _json_error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="Request payload violates the input contract.",
        details=details,
    )


def _domain_error_response(exc: CarbonTrackerDomainError, code: str) -> JSONResponse:
    return _json_error(status.HTTP_400_BAD_REQUEST, code=code, message=str(exc))


async def _handle_invalid_trip(_: Request, exc: InvalidTripError) -> JSONResponse:
    """Traduce invariantes de dominio violadas a 400."""
    return _domain_error_response(exc, "INVALID_TRIP")


async def _handle_unsupported_vehicle_type(
    _: Request,
    exc: UnsupportedVehicleTypeError,
) -> JSONResponse:
    """Traduce tipos de vehiculo sin factor registrado a 400 explicito."""
    return _domain_error_response(exc, "UNSUPPORTED_VEHICLE_TYPE")


async def _handle_domain_error(_: Request, exc: CarbonTrackerDomainError) -> JSONResponse:
    """Red de seguridad para futuros errores de dominio aun no mapeados."""
    return _domain_error_response(exc, "DOMAIN_ERROR")


def register_error_handlers(app: FastAPI) -> None:
    """Registra todos los manejadores; llamado desde la app factory."""
    app.add_exception_handler(RequestValidationError, _handle_request_validation_error)
    app.add_exception_handler(InvalidTripError, _handle_invalid_trip)
    app.add_exception_handler(UnsupportedVehicleTypeError, _handle_unsupported_vehicle_type)
    app.add_exception_handler(CarbonTrackerDomainError, _handle_domain_error)
