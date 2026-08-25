"""Punto de entrada del servicio. Ensambla la app; no contiene logica."""

from fastapi import FastAPI

from carbon_tracker.api.error_handlers import register_error_handlers
from carbon_tracker.api.routes import router as emissions_router


def create_app() -> FastAPI:
    """Construye la aplicacion con routers y manejadores registrados."""
    app = FastAPI(
        title="Carbon Tracker Service",
        summary="Calculo de emisiones estimadas de CO2 para viajes logisticos.",
        version="0.1.0",
    )
    app.include_router(emissions_router)
    register_error_handlers(app)
    return app


app = create_app()
