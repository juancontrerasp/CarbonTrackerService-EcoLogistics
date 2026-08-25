"""Calculo de emisiones de CO2 para viajes logisticos.

MODELO ACADEMICO PROVISIONAL: el requisito original no define la formula.
La forma algebraica y sus coeficientes son supuestos documentados en el
README y marcados con ASSUMPTION. Cuando se apruebe la formula definitiva,
este modulo es el UNICO punto a modificar.
"""

from dataclasses import dataclass
from typing import Final

from carbon_tracker.domain.emission_factors import EmissionFactorProvider
from carbon_tracker.domain.models import Trip

# ASSUMPTION (modelo academico): penalizacion lineal de carga, en kg CO2/km
# por tonelada transportada (~0.8 L/100km extra por tonelada en diesel).
LOAD_SENSITIVITY_KG_CO2_PER_KM_PER_TON: Final[float] = 0.02


@dataclass(frozen=True, slots=True)
class EmissionResult:
    """Resultado del calculo con desglose, en precision completa (sin redondear)."""

    base_emissions_kg: float
    load_penalty_kg: float
    total_kg: float


class EmissionCalculator:
    """Aplica la formula del modelo academico sobre un viaje valido.

    Formula: co2_kg = EF(tipo) * distancia_km * (1 + sensibilidad_carga *
    peso_tons) * efficiency_factor

    La distancia en 0 produce 0 emisiones por la propia aritmetica: no hay
    caso especial codificado.
    """

    def __init__(self, factor_provider: EmissionFactorProvider) -> None:
        self._factor_provider = factor_provider

    def calculate(self, trip: Trip) -> EmissionResult:
        """Calcula las emisiones totales y su desglose para el viaje dado."""
        base_factor = self._factor_provider.get_base_emission_factor(trip.vehicle_type)
        activity_emissions_kg = base_factor * trip.distance_km * trip.efficiency_factor
        load_multiplier = (
            1.0 + LOAD_SENSITIVITY_KG_CO2_PER_KM_PER_TON * trip.cargo_weight_tons
        )
        base_emissions_kg = activity_emissions_kg
        load_penalty_kg = activity_emissions_kg * (load_multiplier - 1.0)
        total_kg = activity_emissions_kg * load_multiplier
        return EmissionResult(
            base_emissions_kg=base_emissions_kg,
            load_penalty_kg=load_penalty_kg,
            total_kg=total_kg,
        )
