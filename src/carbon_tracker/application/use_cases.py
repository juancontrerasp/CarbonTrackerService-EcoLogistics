"""Casos de uso de la aplicacion: orquestan dominio sin conocer HTTP."""

from carbon_tracker.domain.calculator import EmissionCalculator, EmissionResult
from carbon_tracker.domain.models import Trip, VehicleType


class CalculateEmissionsUseCase:
    """Coordina la construccion del viaje (validacion de invariantes) y su calculo."""

    def __init__(self, calculator: EmissionCalculator) -> None:
        self._calculator = calculator

    def execute(
        self,
        *,
        vehicle_type: VehicleType,
        cargo_weight_tons: float,
        distance_km: float,
        efficiency_factor: float,
    ) -> EmissionResult:
        """Construye el ``Trip`` (valida invariantes) y calcula sus emisiones.

        Lanza ``InvalidTripError`` si los datos incumplen las reglas del
        dominio; el mapeo a HTTP ocurre en otra capa.
        """
        trip = Trip(
            vehicle_type=vehicle_type,
            cargo_weight_tons=cargo_weight_tons,
            distance_km=distance_km,
            efficiency_factor=efficiency_factor,
        )
        return self._calculator.calculate(trip)
