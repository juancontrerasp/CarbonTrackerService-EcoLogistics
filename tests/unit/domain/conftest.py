"""Fixture compartido: constructor de viajes validos con overrides."""

from collections.abc import Callable

import pytest

from carbon_tracker.domain.models import Trip, VehicleType


@pytest.fixture
def build_trip() -> Callable[..., Trip]:
    """Devuelve una funcion que construye ``Trip`` validos con overrides.

    Unica fuente de fixtures de dominio para toda la suite unitaria.
    """

    def _build(**overrides: object) -> Trip:
        defaults: dict[str, object] = {
            "vehicle_type": VehicleType.DIESEL,
            "cargo_weight_tons": 5.0,
            "distance_km": 100.0,
            "efficiency_factor": 1.0,
        }
        return Trip(**(defaults | overrides))  # type: ignore[arg-type]

    return _build
