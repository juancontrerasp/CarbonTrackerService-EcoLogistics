"""Tests de integracion: validacion de factores al arranque."""

from unittest.mock import patch

import pytest

from carbon_tracker.main import create_app


class TestStartupValidation:
    """FIX #1: la app valida la tabla de factores al arranque, no en la primera peticion."""

    def test_create_app_validates_emission_factors(self) -> None:
        with patch(
            "carbon_tracker.main.get_static_emission_factor_provider"
        ) as mock_validate:
            create_app()
            mock_validate.assert_called_once()

    def test_create_app_fails_fast_on_incomplete_table(self) -> None:
        from carbon_tracker.domain.emission_factors import StaticEmissionFactorProvider
        from carbon_tracker.domain.errors import UnsupportedVehicleTypeError

        incomplete = StaticEmissionFactorProvider({})

        with (
            patch(
                "carbon_tracker.main.get_static_emission_factor_provider",
                side_effect=incomplete.assert_covers_all_types,
            ),
            pytest.raises(UnsupportedVehicleTypeError),
        ):
            create_app()
