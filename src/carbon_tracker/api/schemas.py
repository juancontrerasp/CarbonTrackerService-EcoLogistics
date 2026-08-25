"""Contrato HTTP de entrada/salida modelado con Pydantic.

Los esquemas solo validan sintaxis y rangos del contrato (422). Las
invariantes semanticas viven en el dominio; los limites numericos se importan
de ahi para que exista una unica fuente de verdad.
"""

from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

from carbon_tracker.domain.calculator import EmissionResult
from carbon_tracker.domain.models import (
    MAX_CARGO_WEIGHT_TONS,
    MAX_EFFICIENCY_FACTOR,
    MAX_TRIP_DISTANCE_KM,
    VehicleType,
)

_DECIMAL_PLACES_KG: Final[int] = 2


def _round_kg(value_kg: float) -> float:
    """Redondea una magnitud en kg CO2 segun el contrato HTTP.

    El redondeo ocurre SOLO aqui (frontera); el dominio opera con precision
    completa.
    """
    return round(value_kg, _DECIMAL_PLACES_KG)


class TripRequest(BaseModel):
    """Cuerpo de peticion para el calculo de emisiones."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "vehicle_type": "diesel",
                    "cargo_weight_tons": 5,
                    "distance_km": 100,
                    "efficiency_factor": 1.0,
                }
            ]
        },
    )

    vehicle_type: VehicleType
    cargo_weight_tons: float = Field(ge=0, le=MAX_CARGO_WEIGHT_TONS, allow_inf_nan=False)
    distance_km: float = Field(ge=0, le=MAX_TRIP_DISTANCE_KM, allow_inf_nan=False)
    efficiency_factor: float = Field(gt=0, le=MAX_EFFICIENCY_FACTOR, allow_inf_nan=False)

    @field_validator(
        "cargo_weight_tons", "distance_km", "efficiency_factor", mode="before"
    )
    @classmethod
    def reject_non_number_types(cls, value: object) -> object:
        """Rechaza strings y booleanos donde se espera un numero JSON.

        ``bool`` es subclase de ``int`` y Pydantic lax lo coaccionaria a
        0.0/1.0: un peso ``true`` no tiene sentido fisico ni contractual.
        """
        if isinstance(value, str):
            raise ValueError("numeric fields must be JSON numbers, not strings")
        if isinstance(value, bool):
            raise ValueError("numeric fields must be JSON numbers, not booleans")
        return value


class EmissionsBreakdown(BaseModel):
    """Desglose de la contribucion de cada termino de la formula."""

    base_emissions_kg: float
    load_penalty_kg: float


class EmissionsResponse(BaseModel):
    """Estimacion total de emisiones junto a su desglose."""

    vehicle_type: VehicleType
    estimated_co2_kg: float
    breakdown: EmissionsBreakdown

    @classmethod
    def from_result(cls, vehicle_type: VehicleType, result: EmissionResult) -> "EmissionsResponse":
        """Mapea un resultado de dominio a la respuesta HTTP redondeada."""
        return cls(
            vehicle_type=vehicle_type,
            estimated_co2_kg=_round_kg(result.total_kg),
            breakdown=EmissionsBreakdown(
                base_emissions_kg=_round_kg(result.base_emissions_kg),
                load_penalty_kg=_round_kg(result.load_penalty_kg),
            ),
        )
