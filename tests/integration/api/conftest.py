"""Fixtures compartidos de la suite de integracion HTTP."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from carbon_tracker.main import create_app

ENDPOINT = "/api/v1/emissions/calculate"


@pytest.fixture
def endpoint() -> str:
    """Ruta del endpoint bajo prueba (unica fuente en la suite)."""
    return ENDPOINT


@pytest.fixture
def diesel_payload() -> dict:
    """Payload valido base; cada test recibe una copia fresca."""
    return {
        "vehicle_type": "diesel",
        "cargo_weight_tons": 5,
        "distance_km": 100,
        "efficiency_factor": 1.0,
    }


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(create_app())
