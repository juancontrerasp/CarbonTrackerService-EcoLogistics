"""Endpoints HTTP del servicio. Delegan en la aplicacion: cero logica de negocio."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from carbon_tracker.api.dependencies import get_calculate_emissions_use_case
from carbon_tracker.api.schemas import EmissionsResponse, TripRequest
from carbon_tracker.application.use_cases import CalculateEmissionsUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["emissions"])


@router.post("/emissions/calculate")
async def calculate_trip_emissions(
    request: TripRequest,
    use_case: Annotated[
        CalculateEmissionsUseCase,
        Depends(get_calculate_emissions_use_case),
    ],
) -> EmissionsResponse:
    """Calcula las emisiones estimadas de CO2 de un viaje logistico."""
    logger.info(
        "Calculating emissions: vehicle=%s, distance=%.1f km, cargo=%.1f t",
        request.vehicle_type.value,
        request.distance_km,
        request.cargo_weight_tons,
    )
    result = use_case.execute(
        vehicle_type=request.vehicle_type,
        cargo_weight_tons=request.cargo_weight_tons,
        distance_km=request.distance_km,
        efficiency_factor=request.efficiency_factor,
    )
    logger.info(
        "Emissions calculated: vehicle=%s, total=%.2f kg CO2",
        request.vehicle_type.value,
        result.total_kg,
    )
    return EmissionsResponse.from_result(request.vehicle_type, result)
