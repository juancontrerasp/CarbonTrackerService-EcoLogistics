"""Tests unitarios de los schemas Pydantic: contrato HTTP sin levantar servidor.

REQUISITO QUE VALIDA ESTE GRUPO:
"Campos obligatorios ausentes", "Tipos de datos incorrectos",
"Tipo de vehiculo vacio/inexistente", "Valores extremadamente grandes"
y el redondeo del contrato de salida.
"""

from math import inf, nan

import pytest
from pydantic import ValidationError

from carbon_tracker.api.schemas import EmissionsResponse, TripRequest
from carbon_tracker.domain.calculator import EmissionResult
from carbon_tracker.domain.models import VehicleType

VALID_PAYLOAD = {
    "vehicle_type": "diesel",
    "cargo_weight_tons": 5,
    "distance_km": 100,
    "efficiency_factor": 1.0,
}


class TestTripRequestValidPayloads:
    """Entradas validas deben construir el DTO (incluida coercion int->float)."""

    def test_accepts_valid_payload(self) -> None:
        request = TripRequest(**VALID_PAYLOAD)

        assert request.vehicle_type is VehicleType.DIESEL
        assert request.cargo_weight_tons == 5.0

    def test_accepts_json_integers_for_float_fields(self) -> None:
        # El JSON "5" (int) es aceptable; el string "5" no.
        request = TripRequest(**VALID_PAYLOAD)

        assert isinstance(request.distance_km, float)

    @pytest.mark.parametrize("vehicle_type", ["electric", "diesel", "hybrid"])
    def test_accepts_every_supported_vehicle_type(self, vehicle_type: str) -> None:
        payload = {**VALID_PAYLOAD, "vehicle_type": vehicle_type}

        assert TripRequest(**payload).vehicle_type.value == vehicle_type


class TestTripRequestMissingFields:
    """Todo campo obligatorio ausente debe ser rechazado con 422 equivalente."""

    @pytest.mark.parametrize(
        "missing_field",
        ["vehicle_type", "cargo_weight_tons", "distance_km", "efficiency_factor"],
    )
    def test_missing_any_required_field_raises(self, missing_field: str) -> None:
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != missing_field}

        with pytest.raises(ValidationError, match=missing_field):
            TripRequest(**payload)


class TestTripRequestWrongTypes:
    """Strings y booleanos NO son numeros; bool es subclase de int en Python."""

    @pytest.mark.parametrize("bad_value", ["5", True, False])
    def test_numeric_fields_reject_strings_and_booleans(self, bad_value: object) -> None:
        with pytest.raises(ValidationError):
            TripRequest(**{**VALID_PAYLOAD, "cargo_weight_tons": bad_value})

    @pytest.mark.parametrize("bad_type", [None, 123, "", "DIESEL", "spaceship"])
    def test_vehicle_type_rejects_non_member_values(self, bad_type: object) -> None:
        with pytest.raises(ValidationError):
            TripRequest(**{**VALID_PAYLOAD, "vehicle_type": bad_type})

    def test_unknown_extra_field_is_forbidden(self) -> None:
        with pytest.raises(ValidationError, match="distnace_km"):
            TripRequest(**{**VALID_PAYLOAD, "distnace_km": 100})


class TestTripRequestRangesAndFiniteness:
    """Guardarrailes numericos y rechazo de NaN/infinitos."""

    @pytest.mark.parametrize("field_name", ["cargo_weight_tons", "distance_km"])
    def test_negative_values_raise(self, field_name: str) -> None:
        with pytest.raises(ValidationError):
            TripRequest(**{**VALID_PAYLOAD, field_name: -0.5})

    def test_zero_efficiency_factor_raises(self) -> None:
        with pytest.raises(ValidationError):
            TripRequest(**{**VALID_PAYLOAD, "efficiency_factor": 0})

    @pytest.mark.parametrize("bad_number", [nan, inf, -inf])
    def test_non_finite_values_raise(self, bad_number: float) -> None:
        with pytest.raises(ValidationError):
            TripRequest(**{**VALID_PAYLOAD, "distance_km": bad_number})

    @pytest.mark.parametrize(
        "field_name, limit",
        [
            ("cargo_weight_tons", 100.001),
            ("distance_km", 10_000.001),
            ("efficiency_factor", 10.001),
        ],
    )
    def test_values_above_guardrails_raise(self, field_name: str, limit: float) -> None:
        with pytest.raises(ValidationError):
            TripRequest(**{**VALID_PAYLOAD, field_name: limit})

    @pytest.mark.parametrize(
        "field_name, boundary",
        [("cargo_weight_tons", 100.0), ("distance_km", 10_000.0), ("efficiency_factor", 10.0)],
    )
    def test_exact_boundaries_are_accepted(self, field_name: str, boundary: float) -> None:
        assert TripRequest(**{**VALID_PAYLOAD, field_name: boundary})


class TestEmissionsResponseMapping:
    """El redondeo a 2 decimales ocurre SOLO en la frontera HTTP."""

    def test_rounds_result_to_two_decimals(self) -> None:
        result = EmissionResult(base_emissions_kg=90.004, load_penalty_kg=9.002, total_kg=99.006)

        response = EmissionsResponse.from_result(VehicleType.DIESEL, result)

        assert response.estimated_co2_kg == 99.01
        assert response.breakdown.base_emissions_kg == 90.0
        assert response.breakdown.load_penalty_kg == 9.0

    def test_tiny_positive_total_is_presented_as_zero(self) -> None:
        # Comportamiento documentado: < 0.005 kg se muestra como 0.0.
        result = EmissionResult(base_emissions_kg=0.00009, load_penalty_kg=0.0, total_kg=0.00009)

        response = EmissionsResponse.from_result(VehicleType.ELECTRIC, result)

        assert response.estimated_co2_kg == 0.0
