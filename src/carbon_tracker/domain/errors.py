"""Excepciones del dominio de calculo de emisiones."""


class CarbonTrackerDomainError(Exception):
    """Base comun para errores provocados por reglas de negocio."""


class InvalidTripError(CarbonTrackerDomainError):
    """Un viaje incumple alguna invariante del dominio."""


class UnsupportedVehicleTypeError(CarbonTrackerDomainError):
    """El tipo de vehículo no tiene factores de emisión registrados."""
