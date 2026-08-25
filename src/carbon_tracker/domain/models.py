"""Modelos de dominio: tipos de vehiculo y viaje con sus invariantes."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Final

from carbon_tracker.domain.errors import InvalidTripError

# Guardarrailes de sanidad (no son requisitos del negocio): acotan entradas
# absurdas que indican un error del cliente. Ajustables si el negocio lo pide.
MAX_CARGO_WEIGHT_TONS: Final[float] = 100.0
MAX_TRIP_DISTANCE_KM: Final[float] = 10_000.0
MAX_EFFICIENCY_FACTOR: Final[float] = 10.0


class VehicleType(StrEnum):
    """Tipos de vehículo soportados por el servicio."""

    ELECTRIC = "electric"
    DIESEL = "diesel"
    HYBRID = "hybrid"


@dataclass(frozen=True, slots=True)
class Trip:
    """Viaje logistico como objeto-valor inmutable.

    El dominio valida sus invariantes aunque la capa HTTP ya haya validado:
    nunca confia en quien lo construye (defensa en profundidad).
    """

    vehicle_type: VehicleType
    cargo_weight_tons: float
    distance_km: float
    efficiency_factor: float

    def __post_init__(self) -> None:
        _validate_vehicle_type(self.vehicle_type)
        _validate_cargo_weight(self.cargo_weight_tons)
        _validate_distance(self.distance_km)
        _validate_efficiency_factor(self.efficiency_factor)


def _validate_vehicle_type(vehicle_type: object) -> None:
    """Excluye valores que no sean miembros del enum soportado."""
    if not isinstance(vehicle_type, VehicleType):
        supported = ", ".join(f"'{vt.value}'" for vt in VehicleType)
        raise InvalidTripError(
            f"vehicle_type must be one of [{supported}], got {type(vehicle_type).__name__}"
        )


def _reject_non_numeric(value: object, field_name: str) -> None:
    """Excluye tipos no numericos antes de cualquier chequeo de rango.

    ``bool`` es subclase de ``int``: sin este guardia, un ``True`` pasaria
    ``isfinite`` como 1.0. Un ``str``, ademas, haria fallar ``isfinite`` con
    un TypeError crudo en lugar de un error de dominio tipado.
    """
    if isinstance(value, (str, bool)):
        raise InvalidTripError(
            f"{field_name} must be a JSON number, got {type(value).__name__}"
        )
    if not isinstance(value, (int, float)):
        raise InvalidTripError(
            f"{field_name} must be a JSON number, got {type(value).__name__}"
        )


def _validate_cargo_weight(cargo_weight_tons: float) -> None:
    _reject_non_numeric(cargo_weight_tons, "cargo_weight_tons")
    if not isfinite(cargo_weight_tons) or not 0.0 <= cargo_weight_tons <= MAX_CARGO_WEIGHT_TONS:
        raise InvalidTripError(
            f"cargo_weight_tons must be a finite value between 0 "
            f"and {MAX_CARGO_WEIGHT_TONS}, got {cargo_weight_tons}"
        )


def _validate_distance(distance_km: float) -> None:
    _reject_non_numeric(distance_km, "distance_km")
    if not isfinite(distance_km) or not 0.0 <= distance_km <= MAX_TRIP_DISTANCE_KM:
        raise InvalidTripError(
            f"distance_km must be a finite value between 0 "
            f"and {MAX_TRIP_DISTANCE_KM}, got {distance_km}"
        )


def _validate_efficiency_factor(efficiency_factor: float) -> None:
    _reject_non_numeric(efficiency_factor, "efficiency_factor")
    if not isfinite(efficiency_factor) or not 0.0 < efficiency_factor <= MAX_EFFICIENCY_FACTOR:
        raise InvalidTripError(
            f"efficiency_factor must be a finite value in the range (0, "
            f"{MAX_EFFICIENCY_FACTOR}], got {efficiency_factor}"
        )
