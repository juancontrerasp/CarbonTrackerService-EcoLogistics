"""Tests unitarios de los manejadores de error HTTP.

REQUISITO QUE VALIDA ESTE GRUPO:
"Manejo centralizado de errores": cada excepcion de dominio se mapea a su
codigo HTTP/codigo de aplicacion sin pasar por el servidor (invocacion directa
de handlers async). Cubre la red de seguridad DOMAIN_ERROR, hoy inalcanzable
vía HTTP.
"""

import asyncio

from fastapi import FastAPI

from carbon_tracker.api import error_handlers
from carbon_tracker.api.error_handlers import register_error_handlers
from carbon_tracker.domain.errors import (
    CarbonTrackerDomainError,
    InvalidTripError,
    UnsupportedVehicleTypeError,
)


def _run(handler, exc: Exception) -> object:
    return asyncio.run(handler(None, exc))  # type: ignore[arg-type]


class TestDomainErrorHandlers:
    def test_invalid_trip_maps_to_400_with_code(self) -> None:
        response = _run(error_handlers._handle_invalid_trip, InvalidTripError("bad weight"))

        assert response.status_code == 400
        assert response.body == b'{"error":{"code":"INVALID_TRIP","message":"bad weight"}}'

    def test_unsupported_vehicle_type_maps_to_400(self) -> None:
        exc = UnsupportedVehicleTypeError("no factor for 'spaceship'")

        response = _run(error_handlers._handle_unsupported_vehicle_type, exc)

        assert response.status_code == 400
        assert b"UNSUPPORTED_VEHICLE_TYPE" in response.body

    def test_fallback_domain_error_maps_to_400_domain_error(self) -> None:
        # Red de seguridad: futuros errores de dominio aun sin mapeo propio.
        response = _run(error_handlers._handle_domain_error, CarbonTrackerDomainError("boom"))

        assert response.status_code == 400
        assert b"DOMAIN_ERROR" in response.body


class TestHelpers:
    def test_field_location_ignores_body_prefix(self) -> None:
        assert error_handlers._field_from_location(("body", "cargo_weight_tons")) == (
            "cargo_weight_tons"
        )

    def test_error_body_omits_details_key_when_empty(self) -> None:
        body = error_handlers._error_body("X", "msg")

        assert body == {"error": {"code": "X", "message": "msg"}}


class TestRegistration:
    def test_register_error_handlers_wires_all_mappings(self) -> None:
        app = FastAPI()

        register_error_handlers(app)

        registered_handlers = set(app.exception_handlers.values())
        expected = {
            error_handlers._handle_request_validation_error,
            error_handlers._handle_invalid_trip,
            error_handlers._handle_unsupported_vehicle_type,
            error_handlers._handle_domain_error,
        }
        assert expected <= registered_handlers
