"""Proveedores de factores de emision base por tipo de vehiculo."""

from collections.abc import Mapping
from typing import Final, Protocol

from carbon_tracker.domain.errors import UnsupportedVehicleTypeError
from carbon_tracker.domain.models import VehicleType

# ASSUMPTION (modelo academico): factores base en kg CO2 por km en condiciones
# de referencia (eficiencia nominal, carga estandar). Valores ilustrativos,
# simplificados a partir de metodologias tipo DEFRA/GLEC; NO certificados.
# electric = 0 por decision tank-to-wheel. Pendientes de sustitucion cuando el
# negocio defina valores oficiales.
BASE_EMISSION_FACTORS_KG_CO2_PER_KM: Final[Mapping[VehicleType, float]] = {
    VehicleType.ELECTRIC: 0.0,
    VehicleType.DIESEL: 0.90,
    VehicleType.HYBRID: 0.55,
}


class EmissionFactorProvider(Protocol):
    """Fuente de factores de emision base (kg CO2/km) por tipo de vehiculo."""

    def get_base_emission_factor(self, vehicle_type: VehicleType) -> float:
        """Devuelve el factor base asociado al tipo de vehiculo."""
        ...


class StaticEmissionFactorProvider:
    """Proveedor respaldado por una tabla estatica definida en codigo.

    Anadir un nuevo tipo de vehiculo = nuevo miembro en el enum del dominio +
    una entrada en esta tabla (o inyectando otra tabla). Sin ramas if/else.
    """

    def __init__(self, factors: Mapping[VehicleType, float] | None = None) -> None:
        self._factors: Mapping[VehicleType, float] = (
            BASE_EMISSION_FACTORS_KG_CO2_PER_KM if factors is None else dict(factors)
        )

    def get_base_emission_factor(self, vehicle_type: VehicleType) -> float:
        """Devuelve el factor del tipo indicado o falla de forma explicita."""
        try:
            return self._factors[vehicle_type]
        except KeyError as error:
            raise UnsupportedVehicleTypeError(
                f"No emission factor registered for vehicle type '{vehicle_type.value}'"
            ) from error

    def assert_covers_all_types(self) -> None:
        """Falla si algun tipo soportado carece de factor.

        Pensado para invocarse en el arranque: una configuracion incompleta
        es un error de despliegue, no del cliente.
        """
        missing = [vt.value for vt in VehicleType if vt not in self._factors]
        if missing:
            raise UnsupportedVehicleTypeError(
                f"Emission factor table is incomplete; missing vehicle types: "
                f"{', '.join(missing)}"
            )
