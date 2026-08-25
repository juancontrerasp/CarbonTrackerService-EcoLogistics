"""Tests de integracion: matriz de aceptacion A1-A9 del contrato."""

from fastapi.testclient import TestClient


def test_a1_diesel_valid_trip_is_positive(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    # Ejemplo 1: positivo; valor exacto fijado por el modelo academico.
    response = client.post(endpoint, json=diesel_payload)
    body = response.json()

    assert response.status_code == 200
    assert body["estimated_co2_kg"] > 0
    assert body["estimated_co2_kg"] == 99.0
    assert body["breakdown"] == {"base_emissions_kg": 90.0, "load_penalty_kg": 9.0}
    assert body["vehicle_type"] == "diesel"


def test_a2_electric_vehicle_uses_its_own_rules(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    # Ejemplo 2: tank-to-wheel, independiente de peso y eficiencia.
    payload = {**diesel_payload, "vehicle_type": "electric", "cargo_weight_tons": 2,
               "efficiency_factor": 0.8}

    response = client.post(endpoint, json=payload)

    assert response.status_code == 200
    assert response.json()["estimated_co2_kg"] == 0.0


def test_a3_zero_distance_diesel_yields_zero_emissions(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    # Ejemplo 3: distancia 0 es valida y produce 0 (HTTP 200, no error).
    response = client.post(endpoint, json={**diesel_payload, "distance_km": 0})

    assert response.status_code == 200
    assert response.json()["estimated_co2_kg"] == 0.0


def test_a4_zero_distance_hybrid_yields_zero_emissions(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    payload = {**diesel_payload, "vehicle_type": "hybrid", "distance_km": 0}

    response = client.post(endpoint, json=payload)

    assert response.status_code == 200
    assert response.json()["estimated_co2_kg"] == 0.0


def test_a5_zero_distance_does_not_bypass_validation(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    # Regla R4: distancia 0 no cortocircuita la validacion del resto de campos.
    payload = {**diesel_payload, "distance_km": 0, "cargo_weight_tons": -5}

    response = client.post(endpoint, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_a6_zero_distance_with_unknown_vehicle_rejects(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    payload = {**diesel_payload, "distance_km": 0, "vehicle_type": "spaceship"}

    response = client.post(endpoint, json=payload)

    assert response.status_code == 422


def test_a7_negative_weight_is_rejected(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    # Ejemplo 4.
    response = client.post(
        endpoint, json={**diesel_payload, "cargo_weight_tons": -5}
    )
    fields = [d["field"] for d in response.json()["error"]["details"]]

    assert response.status_code == 422
    assert any("cargo_weight_tons" in field for field in fields)


def test_a8_unknown_vehicle_type_is_rejected(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    # Ejemplo 5: el mensaje debe listar los tipos soportados.
    response = client.post(
        endpoint, json={**diesel_payload, "vehicle_type": "spaceship"}
    )
    message = str(response.json()["error"])

    assert response.status_code == 422
    assert "diesel" in message and "electric" in message and "hybrid" in message


def test_a9_uppercase_vehicle_type_is_case_sensitive(
    client: TestClient, endpoint: str, diesel_payload: dict
) -> None:
    response = client.post(
        endpoint, json={**diesel_payload, "vehicle_type": "DIESEL"}
    )

    assert response.status_code == 422
