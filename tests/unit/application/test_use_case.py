"""Tests unitarios del caso de uso de calculo de emisiones."""

import pytest

from carbon_tracker.application.use_cases import CalculateEmissionsUseCase
from carbon_tracker.domain.calculator import EmissionCalculator
from carbon_tracker.domain.emission_factors import StaticEmissionFactorProvider
from carbon_tracker.domain.errors import InvalidTripError
from carbon_tracker.domain.models import VehicleType


@pytest.fixture
def use_case() -> CalculateEmissionsUseCase:
    return CalculateEmissionsUseCase(EmissionCalculator(StaticEmissionFactorProvider()))


def _execute(use_case: CalculateEmissionsUseCase, **overrides: object):
    kwargs = {
        "vehicle_type": VehicleType.DIESEL,
        "cargo_weight_tons": 5.0,
        "distance_km": 100.0,
        "efficiency_factor": 1.0,
    }
    return use_case.execute(**(kwargs | overrides))


class TestExecute:
    def test_returns_result_with_breakdown_for_valid_trip(self, use_case) -> None:
        result = _execute(use_case)

        assert result.total_kg == pytest.approx(99.0)
        assert result.total_kg == pytest.approx(
            result.base_emissions_kg + result.load_penalty_kg
        )

    def test_propagates_domain_error_on_invalid_input(self, use_case) -> None:
        with pytest.raises(InvalidTripError):
            _execute(use_case, cargo_weight_tons=-5.0)

    def test_electric_trip_produces_zero(self, use_case) -> None:
        result = _execute(
            use_case, vehicle_type=VehicleType.ELECTRIC, efficiency_factor=0.8
        )

        assert result.total_kg == 0.0

    def test_hybrid_trip_produces_positive_total(self, use_case) -> None:
        # REQUISITO: vehiculo hibrido valido => emisiones positivas.
        result = _execute(use_case, vehicle_type=VehicleType.HYBRID)

        assert result.total_kg > 0.0

    def test_maximum_guardrail_inputs_flow_through(self, use_case) -> None:
        # REQUISITO: "Valores muy grandes" dentro de guardarrailes.
        result = _execute(use_case, cargo_weight_tons=100.0, distance_km=10_000.0,
                          efficiency_factor=10.0)

        assert result.total_kg == pytest.approx(270_000.0)

    def test_propagates_error_for_non_member_vehicle_type(self, use_case) -> None:
        # REQUISITO: "Tipo de vehiculo inexistente" en la orquestacion.
        with pytest.raises(InvalidTripError):
            _execute(use_case, vehicle_type="spaceship")
