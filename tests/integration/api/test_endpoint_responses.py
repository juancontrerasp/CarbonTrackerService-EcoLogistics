"""Pruebas HTTP del endpoint: formato, estructura de respuesta y consistencia.

REQUISITOS QUE VALIDAN ESTE GRUPO (puntos 1, 2, 4-9 del contrato de pruebas):
request valida -> 200; JSON malformado -> 4xx; estructura y tipos de la
respuesta; errores con forma identica entre escenarios.

Los casos ya cubiertos por la matriz A1-A9 (tipo invalido, campos ausentes,
valores negativos) viven en test_emissions_endpoint.py y
test_request_contract.py: aqui no se duplican.
"""

from fastapi.testclient import TestClient

EXPECTED_TOP_LEVEL_KEYS = {"vehicle_type", "estimated_co2_kg", "breakdown"}
EXPECTED_BREAKDOWN_KEYS = {"base_emissions_kg", "load_penalty_kg"}


class TestHappyPathResponse:
    def test_valid_request_returns_200_with_json_content_type(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        response = client.post(endpoint, json=diesel_payload)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_response_structure_matches_contract(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        body = client.post(endpoint, json=diesel_payload).json()

        assert set(body) == EXPECTED_TOP_LEVEL_KEYS
        assert set(body["breakdown"]) == EXPECTED_BREAKDOWN_KEYS
        # Ninguna envolvente de error en una respuesta de exito.
        assert "error" not in body

    def test_response_field_types_are_correct(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        body = client.post(endpoint, json=diesel_payload).json()

        assert isinstance(body["vehicle_type"], str)
        assert isinstance(body["estimated_co2_kg"], float)
        assert isinstance(body["breakdown"], dict)
        assert all(
            isinstance(value, float) for value in body["breakdown"].values()
        )


class TestMalformedJsonBody:
    """Punto 6: el cuerpo no parseable no debe colgar ni devolver 500."""

    def test_syntactically_broken_json_returns_uniform_422(
        self, client: TestClient, endpoint: str
    ) -> None:
        response = client.post(
            endpoint,
            content=b'{"vehicle_type": "diesel", ',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_empty_body_returns_422(self, client: TestClient, endpoint: str) -> None:
        response = client.post(
            endpoint, content=b"", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_non_object_json_returns_422(self, client: TestClient, endpoint: str) -> None:
        response = client.post(
            endpoint, content=b'[1, 2, 3]', headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestErrorConsistency:
    """Punto 9: todo fallo 4xx comparte la misma envolvente {code, message, details}."""

    def test_all_validation_failures_share_identical_envelope_shape(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        scenarios = {
            "negative_value": {**diesel_payload, "distance_km": -5},
            "unknown_vehicle": {**diesel_payload, "vehicle_type": "spaceship"},
            "boolean_in_numeric": {**diesel_payload, "cargo_weight_tons": True},
            "missing_field": {
                k: v for k, v in diesel_payload.items() if k != "efficiency_factor"
            },
        }

        envelopes = []
        for payload in scenarios.values():
            response = client.post(endpoint, json=payload)
            assert response.status_code == 422
            envelopes.append(response.json()["error"])

        assert all(set(envelope) == {"code", "message", "details"} for envelope in envelopes)
        assert all(e["code"] == "VALIDATION_ERROR" for e in envelopes)

    def test_malformed_json_and_invalid_data_share_same_envelope_code(
        self, client: TestClient, endpoint: str, diesel_payload: dict
    ) -> None:
        broken = client.post(
            endpoint,
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
        invalid_data = client.post(endpoint, json={**diesel_payload, "distance_km": -1})

        assert broken.json()["error"]["code"] == invalid_data.json()["error"]["code"]
