"""Punto de entrada del servicio. Ensambla la app; no contiene logica."""

import logging

from fastapi import FastAPI

from carbon_tracker.api.dependencies import get_static_emission_factor_provider
from carbon_tracker.api.error_handlers import register_error_handlers
from carbon_tracker.api.routes import router as emissions_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Construye la aplicacion con routers y manejadores registrados."""
    app = FastAPI(
        title="Carbon Tracker Service",
        summary="Calculo de emisiones estimadas de CO2 para viajes logisticos.",
        version="0.1.0",
    )
    app.include_router(emissions_router)
    register_error_handlers(app)
    _validate_emission_factors_at_startup()
    return app


def _validate_emission_factors_at_startup() -> None:
    """Eagerly inicializa y valida la tabla de factores de emision.

    Si la tabla esta incompleta (typo en enum, factor olvidado), la app
    falla aqui, en el arranque, en vez de en la primera peticion.
    """
    get_static_emission_factor_provider()
    logger.info("Emission factor table validated successfully.")


app = create_app()
