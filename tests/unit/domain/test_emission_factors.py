"""Verifica que la tabla de factores cubre todos los tipos soportados."""

import pytest

from carbon_tracker.domain.emission_factors import (
    BASE_EMISSION_FACTORS_KG_CO2_PER_KM,
    StaticEmissionFactorProvider,
)
from carbon_tracker.domain.errors import UnsupportedVehicleTypeError
from carbon_tracker.domain.models import VehicleType


@pytest.fixture
def provider() -> StaticEmissionFactorProvider:
    return StaticEmissionFactorProvider()


class TestStaticProvider:
    def test_every_supported_vehicle_type_has_a_factor(self, provider) -> None:
        # Guarda: anadir miembro al enum sin factor rompe este test.
        for vehicle_type in VehicleType:
            assert vehicle_type in BASE_EMISSION_FACTORS_KG_CO2_PER_KM
            assert provider.get_base_emission_factor(vehicle_type) >= 0.0

    def test_electric_is_zero_tank_to_wheel(self, provider) -> None:
        assert provider.get_base_emission_factor(VehicleType.ELECTRIC) == 0.0

    def test_documented_reference_values(self, provider) -> None:
        # Fija los supuestos academicos documentados en el README.
        assert provider.get_base_emission_factor(VehicleType.DIESEL) == 0.90
        assert provider.get_base_emission_factor(VehicleType.HYBRID) == 0.55

    def test_missing_factor_raises_domain_error(self) -> None:
        partial_provider = StaticEmissionFactorProvider({VehicleType.ELECTRIC: 0.0})

        with pytest.raises(UnsupportedVehicleTypeError):
            partial_provider.get_base_emission_factor(VehicleType.DIESEL)


class TestStartupFailFast:
    """REQUISITO: configuracion incompleta debe romper el arranque, no una peticion."""

    def test_complete_table_passes_assertion(self, provider) -> None:
        provider.assert_covers_all_types()  # no raise

    def test_incomplete_table_lists_missing_types(self) -> None:
        provider = StaticEmissionFactorProvider({VehicleType.ELECTRIC: 0.0})

        with pytest.raises(UnsupportedVehicleTypeError, match="diesel, hybrid"):
            provider.assert_covers_all_types()


class TestFactorsTableImmutability:
    """FIX #5: la tabla de factores custom no debe ser modificable externamente."""

    def test_custom_factors_table_is_immutable(self) -> None:
        custom = {VehicleType.ELECTRIC: 0.0, VehicleType.DIESEL: 1.5, VehicleType.HYBRID: 0.8}
        provider = StaticEmissionFactorProvider(custom)

        with pytest.raises(TypeError):
            provider._factors[VehicleType.DIESEL] = 999.0  # type: ignore[index]

    def test_default_factors_table_is_immutable(self) -> None:
        provider = StaticEmissionFactorProvider()

        with pytest.raises(TypeError):
            provider._factors[VehicleType.DIESEL] = 999.0  # type: ignore[index]
