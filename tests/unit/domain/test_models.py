"""Tests unitarios del modelo Trip: invariantes de dominio puro, sin HTTP."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from carbon_tracker.domain.errors import InvalidTripError
from carbon_tracker.domain.models import MAX_CARGO_WEIGHT_TONS, Trip, VehicleType

NUMERIC_FIELDS = ("cargo_weight_tons", "distance_km", "efficiency_factor")


class TestValidTrips:
    def test_creates_trip_with_valid_data(self, build_trip: Callable[..., Trip]) -> None:
        trip = build_trip()

        assert trip.vehicle_type is VehicleType.DIESEL
        assert trip.cargo_weight_tons == 5.0
        assert trip.distance_km == 100.0
        assert trip.efficiency_factor == 1.0

    @pytest.mark.parametrize("weight", [0.0, 0.5, 100.0])
    def test_accepts_zero_and_boundary_cargo_weight(
        self, build_trip: Callable[..., Trip], weight: float
    ) -> None:
        assert build_trip(cargo_weight_tons=weight).cargo_weight_tons == weight

    @pytest.mark.parametrize("field_name", NUMERIC_FIELDS)
    def test_accepts_exact_upper_boundary(
        self, build_trip: Callable[..., Trip], field_name: str
    ) -> None:
        boundaries = {
            "cargo_weight_tons": 100.0,
            "distance_km": 10_000.0,
            "efficiency_factor": 10.0,
        }
        assert build_trip(**{field_name: boundaries[field_name]})

    def test_accepts_zero_distance(self, build_trip: Callable[..., Trip]) -> None:
        # Regla A3: distancia 0 es valida (produce 0 emisiones).
        assert build_trip(distance_km=0.0).distance_km == 0.0

    def test_is_immutable(self, build_trip: Callable[..., Trip]) -> None:
        trip = build_trip()

        with pytest.raises(FrozenInstanceError):
            trip.distance_km = 200.0


class TestInvalidRanges:
    @pytest.mark.parametrize("weight", [-5.0, -0.001, 100.001])
    def test_rejects_out_of_range_weight(
        self, build_trip: Callable[..., Trip], weight: float
    ) -> None:
        with pytest.raises(InvalidTripError, match="cargo_weight_tons"):
            build_trip(cargo_weight_tons=weight)

    @pytest.mark.parametrize("distance", [-1.0, -0.001, 10_000.001])
    def test_rejects_out_of_range_distance(
        self, build_trip: Callable[..., Trip], distance: float
    ) -> None:
        with pytest.raises(InvalidTripError, match="distance_km"):
            build_trip(distance_km=distance)

    @pytest.mark.parametrize("factor", [0.0, -1.0, 10.001])
    def test_rejects_out_of_range_efficiency_factor(
        self, build_trip: Callable[..., Trip], factor: float
    ) -> None:
        # eta = 0 implicaria que un diesel no emite: absurdo fisico.
        with pytest.raises(InvalidTripError, match="efficiency_factor"):
            build_trip(efficiency_factor=factor)

    @pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
    def test_rejects_non_finite_values(
        self, build_trip: Callable[..., Trip], bad_value: float
    ) -> None:
        with pytest.raises(InvalidTripError):
            build_trip(cargo_weight_tons=bad_value)


class TestNonNumericTypesRejected:
    """Defensa en profundidad: el dominio tampoco acepta str/bool.

    ``bool`` es subclase de ``int`` y pasaría chequeos numericos si no se
    excluyera explicitamente.
    """

    @pytest.mark.parametrize("field_name", NUMERIC_FIELDS)
    @pytest.mark.parametrize("bad_value", [True, False])
    def test_rejects_booleans_in_numeric_fields(
        self, build_trip: Callable[..., Trip], field_name: str, bad_value: bool
    ) -> None:
        with pytest.raises(InvalidTripError, match="must be a JSON number"):
            build_trip(**{field_name: bad_value})

    @pytest.mark.parametrize("field_name", NUMERIC_FIELDS)
    def test_rejects_strings_in_numeric_fields(
        self, build_trip: Callable[..., Trip], field_name: str
    ) -> None:
        with pytest.raises(InvalidTripError, match="must be a JSON number"):
            build_trip(**{field_name: "100"})

    @pytest.mark.parametrize("field_name", NUMERIC_FIELDS)
    @pytest.mark.parametrize(
        "bad_value",
        [
            {"value": 1},
            [1.0],
            b"1.0",
        ],
    )
    def test_rejects_non_int_float_types_in_numeric_fields(
        self, build_trip: Callable[..., Trip], field_name: str, bad_value: object
    ) -> None:
        """FIX #8: tipos numericos exoticos (dict, list, bytes) rechazados en runtime."""
        with pytest.raises(InvalidTripError, match="must be a JSON number"):
            build_trip(**{field_name: bad_value})


class TestVehicleTypeValidation:
    """REQUISITO: "Tipo de vehiculo inexistente" tambien en el dominio.

    Sin este guardia, ``Trip(vehicle_type="spaceship")`` cruzaba el dominio
    y explotaba mas adelante en el proveedor de factores.
    """

    @pytest.mark.parametrize("bad_type", ["spaceship", "", "DIESEL", 123, None])
    def test_rejects_non_member_vehicle_types(
        self, build_trip: Callable[..., Trip], bad_type: object
    ) -> None:
        with pytest.raises(InvalidTripError, match="vehicle_type must be one of"):
            build_trip(vehicle_type=bad_type)

    def test_error_message_lists_supported_values(
        self, build_trip: Callable[..., Trip]
    ) -> None:
        with pytest.raises(InvalidTripError, match="'electric', 'diesel', 'hybrid'"):
            build_trip(vehicle_type="steam")


def test_max_cargo_weight_is_documented_guardrail() -> None:
    assert MAX_CARGO_WEIGHT_TONS == 100.0
