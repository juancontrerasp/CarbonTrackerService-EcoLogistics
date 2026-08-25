"""Tests de integracion: detalles del contrato HTTP (tipos, limites, forma de error)."""

import pytest
from fastapi.testclient import TestClient


class TestNonNumberTypesRejected:
    @pytest.mark.parametrize("bad_value", ["5", True, False])
    def test_non_numbers_rejected_in_numeric_fields(
        self, client: TestClient, endpoint: str, diesel_payload: dict, bad_value: object
    ) -> None:
        # bool es subclase de int: sin validador explicito se coaccionaria a 0/1.
        response = client.post(
            endpoint, json={**diesel_payload, "cargo_weight_tons": bad_value}
        )

        assert response.status_code == 422

    @pytest.mark.parametrize("bad_type", ["", None, 123])
    def test_invalid_vehicle_type_variants_rejected(
        self, client: TestClient, endpoint: str, diesel_payload: dict, bad_type: object
    ) -> None:
        response = client.post(
            endpoint, json={**diesel_payload, "vehicle_type": bad_type}
        )

        assert response.status_code == 422


class TestOverflowingValues:
    def test_exponential_overflow_distance_rejected(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        # 1e400 parsea a float infinito; JSON estandar no lo transporta,
        # se envia el literal en bruto para ejercitar la defensa del servidor.
        raw = (
            b'{"vehicle_type": "diesel", "cargo_weight_tons": 5, '
            b'"distance_km": 1e400, "efficiency_factor": 1.0}'
        )
        response = client.post(endpoint, content=raw, headers={"Content-Type": "application/json"})

        assert response.status_code == 422

    def test_giant_integer_cargo_weight_rejected(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        raw = (
            b'{"vehicle_type": "diesel", "cargo_weight_tons": '
            + b"9" * 400
            + b', "distance_km": 100, "efficiency_factor": 1.0}'
        )
        response = client.post(endpoint, content=raw, headers={"Content-Type": "application/json"})

        assert response.status_code == 422

    def test_infinity_literal_distance_rejected(self, client: TestClient, endpoint: str) -> None:
        raw = (
            b'{"vehicle_type": "diesel", "cargo_weight_tons": 5, '
            b'"distance_km": Infinity, "efficiency_factor": 1.0}'
        )
        response = client.post(endpoint, content=raw, headers={"Content-Type": "application/json"})

        assert response.status_code == 422


class TestUpperGuardrailsOverHttp:
    def test_exact_upper_boundaries_are_accepted(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        payload = {
            **diesel_payload,
            "cargo_weight_tons": 100,
            "distance_km": 10_000,
            "efficiency_factor": 10,
        }

        response = client.post(endpoint, json=payload)

        assert response.status_code == 200

    def test_cargo_weight_above_boundary_rejected(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        response = client.post(
            endpoint, json={**diesel_payload, "cargo_weight_tons": 100.001}
        )

        assert response.status_code == 422

    def test_efficiency_factor_above_boundary_rejected(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        response = client.post(
            endpoint, json={**diesel_payload, "efficiency_factor": 10.001}
        )

        assert response.status_code == 422


class TestContractDetails:
    def test_missing_field_is_rejected(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        payload = {key: value for key, value in diesel_payload.items() if key != "distance_km"}

        response = client.post(endpoint, json=payload)

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_unknown_extra_field_is_rejected_strictly(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        # Validacion estricta: detecta typos como 'distnace_km' en vez de ignorarlos.
        response = client.post(endpoint, json={**diesel_payload, "distnace_km": 100})

        assert response.status_code == 422

    def test_error_response_shape_is_uniform(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        response = client.post(endpoint, json={**diesel_payload, "distance_km": -1})

        error = response.json()["error"]
        assert set(error) == {"code", "message", "details"}
