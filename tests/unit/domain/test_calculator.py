"""Tests unitarios del calculador de emisiones con proveedor inyectado."""

from collections.abc import Callable

import pytest

from carbon_tracker.domain.calculator import EmissionCalculator
from carbon_tracker.domain.emission_factors import StaticEmissionFactorProvider
from carbon_tracker.domain.models import Trip, VehicleType


class FakeFactorProvider:
    """Proveedor minimo para verificar la inyeccion de dependencias."""

    def __init__(self, factors: dict[VehicleType, float]) -> None:
        self._factors = factors

    def get_base_emission_factor(self, vehicle_type: VehicleType) -> float:
        return self._factors[vehicle_type]


@pytest.fixture
def calculator() -> EmissionCalculator:
    # Tabla real de factores: cubre todos los VehicleType del enum.
    return EmissionCalculator(StaticEmissionFactorProvider())


class TestFormula:
    def test_diesel_reference_example(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        # Ejemplo 1 del contrato: 0.90 * 100 * (1 + 0.02*5) * 1.0 = 99.0
        result = calculator.calculate(build_trip())

        assert result.base_emissions_kg == pytest.approx(90.0)
        assert result.load_penalty_kg == pytest.approx(9.0)
        assert result.total_kg == pytest.approx(99.0)

    def test_combustion_vehicle_yields_positive_total(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        assert calculator.calculate(build_trip()).total_kg > 0.0

    def test_zero_distance_yields_zero_total_for_any_type(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        # Regla A3/A4: sin caso especial, la aritmetica lo garantiza.
        for vehicle_type in VehicleType:
            result = calculator.calculate(
                build_trip(vehicle_type=vehicle_type, distance_km=0.0)
            )
            assert result.total_kg == 0.0

    def test_distance_proportionality(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        short = calculator.calculate(build_trip(distance_km=100.0)).total_kg
        long = calculator.calculate(build_trip(distance_km=200.0)).total_kg

        assert long == pytest.approx(short * 2)

    def test_efficiency_scales_result_linearly(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        reference = calculator.calculate(build_trip(efficiency_factor=1.0)).total_kg
        degraded = calculator.calculate(build_trip(efficiency_factor=1.1)).total_kg

        assert degraded == pytest.approx(reference * 1.1)


class TestValidVehiclesByType:
    """REQUISITO: "Vehiculo diesel / electrico / hibrido" con valores validos.

    Fija el total exacto por tipo segun los factores ASSUMPTION documentados.
    """

    @pytest.mark.parametrize(
        "vehicle_type, expected_total",
        [
            (VehicleType.DIESEL, pytest.approx(99.0)),  # 0.90 * 100 * 1.1
            (VehicleType.HYBRID, pytest.approx(60.5)),  # 0.55 * 100 * 1.1
        ],
    )
    def test_combustion_types_compute_positive_total(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
        vehicle_type: VehicleType,
        expected_total: object,
    ) -> None:
        result = calculator.calculate(build_trip(vehicle_type=vehicle_type))

        assert result.total_kg == expected_total
        assert result.total_kg > 0.0

    def test_breakdown_sums_exactly_to_total(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        for vehicle_type in VehicleType:
            result = calculator.calculate(build_trip(vehicle_type=vehicle_type))
            assert result.base_emissions_kg + result.load_penalty_kg == pytest.approx(
                result.total_kg
            )


class TestInputValueGrids:
    """REQUISITO: "Diferentes pesos, distancias y factores de eficiencia".

    Rejilla parametrizada contra la formula cerrada del modelo academico.
    """

    @pytest.mark.parametrize(
        "cargo_weight_tons, expected_total",
        [(0.0, 90.0), (1.0, 91.8), (10.0, 108.0), (100.0, 270.0)],
    )
    def test_totals_across_cargo_weights(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
        cargo_weight_tons: float,
        expected_total: float,
    ) -> None:
        result = calculator.calculate(build_trip(cargo_weight_tons=cargo_weight_tons))

        assert result.total_kg == pytest.approx(expected_total)

    @pytest.mark.parametrize(
        "distance_km, expected_total",
        [(1.0, 0.99), (0.5, 0.495), (2_500.0, 2475.0)],
    )
    def test_totals_scale_linearly_with_distance(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
        distance_km: float,
        expected_total: float,
    ) -> None:
        result = calculator.calculate(build_trip(distance_km=distance_km))

        assert result.total_kg == pytest.approx(expected_total)

    @pytest.mark.parametrize(
        "efficiency_factor, expected_total",
        [(0.5, pytest.approx(49.5)), (1.5, pytest.approx(148.5)), (10.0, pytest.approx(990.0))],
    )
    def test_totals_scale_linearly_with_efficiency_factor(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
        efficiency_factor: float,
        expected_total: float,
    ) -> None:
        result = calculator.calculate(build_trip(efficiency_factor=efficiency_factor))

        assert result.total_kg == pytest.approx(expected_total)


class TestBoundaryValues:
    """REQUISITO: "Valores decimales, muy pequenos y muy grandes" (dentro de guardarrailes)."""

    def test_maximum_allowed_inputs_yield_documented_maximum(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        # Maximo posible: 0.9 * 10_000 * (1 + 0.02*100) * 10 = 270_000 kg.
        trip = build_trip(cargo_weight_tons=100.0, distance_km=10_000.0, efficiency_factor=10.0)

        result = calculator.calculate(trip)

        assert result.total_kg == pytest.approx(270_000.0)

    def test_very_small_but_valid_inputs_stay_positive(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        trip = build_trip(distance_km=1e-9, cargo_weight_tons=0.0, efficiency_factor=1e-6)

        result = calculator.calculate(trip)

        assert 0.0 < result.total_kg < 1e-14

    def test_decimal_inputs_are_handled_without_loss_of_shape(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        trip = build_trip(
            cargo_weight_tons=5.123456789, distance_km=100.777, efficiency_factor=0.987
        )

        result = calculator.calculate(trip)

        # Desglose coherente aunque la entrada tenga muchos decimales.
        assert result.base_emissions_kg > 0
        assert result.load_penalty_kg >= 0
        assert result.total_kg == pytest.approx(
            result.base_emissions_kg + result.load_penalty_kg
        )

    def test_zero_cargo_weight_produces_no_load_penalty(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        # REQUISITO: "Peso igual a cero" => solo emisiones base.
        result = calculator.calculate(build_trip(cargo_weight_tons=0.0))

        assert result.load_penalty_kg == 0.0
        assert result.total_kg == pytest.approx(result.base_emissions_kg)


class TestElectricVehicles:
    def test_electric_is_always_zero_regardless_of_inputs(
        self,
        calculator: EmissionCalculator,
        build_trip: Callable[..., Trip],
    ) -> None:
        # Regla A2 / decision tank-to-wheel: eta y peso son irrelevantes.
        result = calculator.calculate(
            build_trip(
                vehicle_type=VehicleType.ELECTRIC,
                cargo_weight_tons=2.0,
                efficiency_factor=0.8,
            )
        )

        assert result.total_kg == 0.0


class TestDependencyInjection:
    def test_uses_injected_provider_factors(
        self, build_trip: Callable[..., Trip]
    ) -> None:
        custom_calculator = EmissionCalculator(
            FakeFactorProvider({VehicleType.DIESEL: 2.0})
        )

        result = custom_calculator.calculate(build_trip(cargo_weight_tons=0.0))

        assert result.total_kg == pytest.approx(200.0)
