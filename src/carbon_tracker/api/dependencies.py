"""Inyeccion de dependencias: cablea las capas sin estado global mutable."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from carbon_tracker.application.use_cases import CalculateEmissionsUseCase
from carbon_tracker.domain.calculator import EmissionCalculator
from carbon_tracker.domain.emission_factors import StaticEmissionFactorProvider


@lru_cache(maxsize=1)
def get_static_emission_factor_provider() -> StaticEmissionFactorProvider:
    """Instancia unica del proveedor estatico, verificada en el arranque."""
    provider = StaticEmissionFactorProvider()
    provider.assert_covers_all_types()
    return provider


def get_emission_calculator(
    factor_provider: Annotated[
        StaticEmissionFactorProvider,
        Depends(get_static_emission_factor_provider),
    ],
) -> EmissionCalculator:
    """Construye el calculador con su proveedor de factores inyectado."""
    return EmissionCalculator(factor_provider)


def get_calculate_emissions_use_case(
    calculator: Annotated[EmissionCalculator, Depends(get_emission_calculator)],
) -> CalculateEmissionsUseCase:
    """Construye el caso de uso con su calculador inyectado."""
    return CalculateEmissionsUseCase(calculator)
