# CarbonTrackerService-EcoLogistics

Microservicio que calcula las emisiones estimadas de CO2 producidas por un vehiculo durante un viaje logistico.

## Stack

Python 3.12+ · FastAPI · Pydantic v2 · Pytest · uv · Ruff

## Puesta en marcha

```bash
uv sync                      # instala dependencias (crea .venv)
uv run pytest -q             # suite de tests (unit + integracion)
uv run ruff check .          # lint
uv run uvicorn carbon_tracker.main:app --reload   # servidor dev
```

Docs interactivas: http://localhost:8000/docs

## Arquitectura

```
src/carbon_tracker/
├── domain/        # Nucleo puro: sin FastAPI ni Pydantic
│   ├── models.py            # VehicleType (StrEnum) + Trip (frozen, invariantes)
│   ├── emission_factors.py  # EmissionFactorProvider (Protocol) + tabla estatica
│   ├── calculator.py        # Formula + EmissionResult con desglose
│   └── errors.py            # Excepciones de dominio
├── application/   # CalculateEmissionsUseCase: orquestacion sin HTTP
├── api/           # Borde HTTP: schemas Pydantic, routes, DI, error handlers
└── main.py        # App factory
```

Flujo: `Request -> routes (validacion sintactica, 422) -> use case (Trip valida invariantes) -> calculator -> EmissionsResponse (redondeo en frontera)`.

El dominio nunca confia en quien lo construye: valida sus propias invariantes aunque la capa HTTP ya haya validado.

## Modelo de calculo

> **MODELO ACADEMICO PROVISIONAL.** El requisito no define la formula; los coeficientes son supuestos documentados, NO valores certificados. La formula definitiva se sustituira unicamente en `domain/calculator.py` y `domain/emission_factors.py`.

```
CO2_kg = EF(tipo_vehiculo) x distancia_km x (1 + 0.02 x peso_tons) x efficiency_factor
```

| Tipo | EF (kg CO2/km) | Nota |
|---|---|---|
| electric | 0.0 | Tank-to-wheel: sin combustion directa |
| diesel | 0.90 | ~33 L/100 km x 2.68 kg CO2/L |
| hybrid | 0.55 | Supuesto: hibrido-diesel (~60% del diesel) |

### Ejemplo

Diesel, 5 t, 100 km, eficiencia 1.0:

```bash
curl -X POST localhost:8000/api/v1/emissions/calculate \
  -H 'Content-Type: application/json' \
  -d '{"vehicle_type":"diesel","cargo_weight_tons":5,"distance_km":100,"efficiency_factor":1.0}'
# {"vehicle_type":"diesel","estimated_co2_kg":99.0,
#  "breakdown":{"base_emissions_kg":90.0,"load_penalty_kg":9.0}}
```

## Reglas de validacion

| Campo | Regla | Violacion |
|---|---|---|
| `vehicle_type` | `electric` \| `diesel` \| `hybrid` (exacto, case-sensitive) | 422 |
| `cargo_weight_tons` | numero JSON finito, `0 <= w <= 100`; strings y booleanos rechazados | 422 |
| `distance_km` | numero JSON finito, `0 <= d <= 10 000` (0 valido => 0 emisiones) | 422 |
| `efficiency_factor` | numero JSON finito, `0 < e <= 10` | 422 |

Detalles del contrato:

- **Campos desconocidos** rechazados (`extra="forbid"`): detecta typos como `distnace_km`.
- **Booleanos en campos numericos rechazados**: `bool` es subclase de `int` en Python; sin validador explicito, `"cargo_weight_tons": true` se coaccionaria a `1.0`.
- **Overflow**: literales no estandar (`Infinity`) o exponenciales desbordados (`1e400`, parsea a infinito) son rechazados por `allow_inf_nan=False`. Enteros gigantes sin representacion float => 422.
- **Decimales**: sin cota arbitraria; float64 limita la precision (~15-17 digitos significativos). La salida se redondea a 2 decimales en la frontera HTTP.
- **Comportamiento conocido del redondeo**: resultados reales menores a 0.005 kg se muestran como `0.0` aunque el dominio garantice un valor positivo.
- Las cotas superiores (100 t / 10 000 km / eta 10) son guardarrailes configurables contra entradas absurdas, con tests de frontera exacta.

## Contrato de errores

Forma uniforme para todo fallo:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": [{"field": "...", "message": "..."}]}}
```

- `VALIDATION_ERROR` (422): contrato HTTP violado (tipos, rangos, enum, extras)
- `INVALID_TRIP` (400): invariante de dominio violada (defensa en profundidad)
- `UNSUPPORTED_VEHICLE_TYPE` (400): tipo de enum sin factor registrado

## Decisiones abiertas / supuestos pendientes del negocio

1. **Formula definitiva**: pendiente; activa la provisional marcada con `ASSUMPTION`.
2. **Semantica de `efficiency_factor`**: interpretacion provisional = multiplicador adimensional (>1 empeora, <1 mejora, 1 = referencia).
3. **Alcance de electricos**: tank-to-wheel (decision tomada); well-to-wheel exigiria factor de red electrica.
4. **Cargas 0 permitidas** (viajes vacios/repositioning) y cotas superiores: propuestas aprobadas como guardarrailes.

## Convenciones y decisiones de diseno

- **Idioma**: docstrings en espanol; mensajes de error e identificadores en ingles (superficie maquina).
- **Strategy pospuesto deliberadamente**: la formula es identica para los tres tipos (solo cambia el EF), asi que basta el registro dict + Protocol. Extraer estrategias por tipo SOLO cuando las formulas diverjan estructuralmente (p.ej. well-to-wheel para electricos).
- **DIP parcial consciente**: `CalculateEmissionsUseCase` depende del calculador concreto (logica pura, instanciable en tests). Se introducira un Protocol si gana colaboradores.
- **Fail-fast en arranque**: `StaticEmissionFactorProvider.assert_covers_all_types()` se invoca al construir la app; un enum con tipo sin factor registrado rompe el despliegue, no la primera peticion.
- **Defensa en profundidad**: las reglas numericas existen en schemas (422) y en dominio (`InvalidTripError` -> 400); los valores limites se importan del dominio, una sola fuente.
