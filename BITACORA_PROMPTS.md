# Bitácora de Prompts — CarbonTrackerService-EcoLogistics

Registro cronológico de todos los prompts realizados durante el desarrollo del microservicio, reproducidos íntegramente, junto con un resumen de la respuesta o código generado en cada iteración.

**Fecha:** 2026-08-25 · **Modelo:** ox-alpha → big-pickle · **Estado final:** 157 tests, ruff limpio, auditoría 8.95/10

## Índice

| # | Tema del prompt | Resultado principal |
|---|---|---|
| 1 | Contexto y rol (pair programmer senior) | Análisis de vacío del repo, ambigüedades detectadas, cuestionario de diseño |
| 2 | Análisis de la lógica de cálculo | Modelo académico de la fórmula, reglas de validación, decisiones arquitectónicas |
| 3 | Ejemplos de comportamiento EJEMPLO 1–5 | Reglas generales R1–R7, matriz de aceptación A1–A9, corrección de mi regla de distancia |
| 4 | Implementación de la primera versión funcional | Servicio completo en capas, 47 tests, README, smoke test |
| 5 | Revisión crítica de validación de entradas | Tabla de 14 casos, bug bool→float confirmado, cambios propuestos |
| 6 | Revisión de diseño y mantenibilidad (SOLID) | Problemas P1–P5, refactor ligero, Strategy pospuesto con justificación |
| 7 | Aprobación («Sí») | Ejecución del paquete combinado: fixes + refactors, 69 tests |
| 8 | Suite completa de pruebas unitarias (≥90%) | Cobertura 100%, +66 tests, agujero vehicle_type en dominio corregido |
| 9 | Pruebas de endpoints FastAPI | 8 tests nuevos (JSON malformado, estructura, tipos, consistencia), 143 tests |
| 10 | Creación de esta bitácora | Este documento |
| 11 | Code review independiente (Senior SWE) | 10 problemas identificados (1 CRITICAL, 2 HIGH, 2 MEDIUM, 5 LOW), puntuación global 8.95/10 |
| 12 | Corrección de problemas del review | 8 problemas corregidos, 14 tests nuevos, 157 tests totales |
| 13 | Auditoría final del proyecto | Evaluación en 10 categorías, checklist de entrega, trazabilidad completa |

---

## Prompt 1 — Definición de contexto y rol

### Prompt completo

> Actúa como un Desarrollador Senior especializado en diseño de microservicios, Python, FastAPI, arquitectura limpia y desarrollo orientado a pruebas.
>
> Estamos construyendo un microservicio llamado "Carbon Tracker Service" para una empresa de logística llamada EcoLogistics.
>
> OBJETIVO DEL MICROSERVICIO:
> Calcular las emisiones estimadas de CO2 producidas por un vehículo durante un viaje logístico.
>
> DATOS DE ENTRADA:
>
> * vehicle_type: tipo de vehículo. Valores permitidos inicialmente: "electric", "diesel", "hybrid".
> * cargo_weight_tons: peso de la carga en toneladas.
> * distance_km: distancia recorrida en kilómetros.
> * efficiency_factor: factor de eficiencia del combustible o energía.
>
> STACK TECNOLÓGICO:
>
> * Python 3.12+
> * FastAPI
> * Pydantic
> * Pytest
> * Arquitectura modular
> * Type hints
> * Ruff/PEP 8 como referencia de estilo
>
> PRINCIPIOS:
>
> * SOLID
> * Separation of Concerns
> * DRY
> * KISS
> * Código legible y mantenible
> * Funciones pequeñas y con una única responsabilidad
> * Validación estricta de entradas
> * Manejo explícito de errores
> * Lógica de negocio independiente de FastAPI
> * Código fácilmente testeable
>
> TU ROL:
> No debes limitarte a generar código. Actúa como un pair programmer senior: cuestiona supuestos, identifica ambigüedades, señala posibles errores de diseño y propone alternativas cuando sea necesario.
>
> RESTRICCIONES:
>
> * No inventes requisitos que no estén definidos sin indicarlo explícitamente.
> * Si falta información necesaria para definir correctamente una fórmula, identifica la ambigüedad antes de implementarla.
> * No mezcles lógica de negocio con los endpoints HTTP.
> * Prioriza una arquitectura sencilla y adecuada para el tamaño del proyecto.
>
> A partir de ahora, utiliza este contexto para todas las tareas relacionadas con este proyecto.

### Respuesta / resultado

Análisis inicial: repositorio vacío (solo README y .gitignore). Ambigüedades bloqueantes identificadas antes de diseñar: (1) la fórmula de emisión no estaba definida, (2) semántica de `efficiency_factor` indeterminada (multiplicador / ratio de consumo / ajuste porcentual), (3) alcance de vehículos eléctricos (tank-to-wheel vs well-to-wheel), (4) persistencia stateless o no. Se propuso un esqueleto de arquitectura en capas (domain/application/api/main) y se plantearon esas dudas mediante cuestionario.

**Decisiones registradas de las respuestas al cuestionario:** fórmula «Analizaremos próximamente»; eficiencia quedó abierta (la respuesta reprodujo el enunciado original); eléctricos = tank-to-wheel; tooling = uv + src layout. Plan de fases 0–4 aprobado (scaffold → dominio TDD → aplicación → API → verificación).

---

## Prompt 2 — Análisis de la lógica de cálculo

### Prompt completo

> Antes de escribir cualquier código, analiza el problema como un desarrollador senior.
>
> Necesitamos definir la lógica para calcular las emisiones de CO2 del Carbon Tracker Service.
>
> Analiza y presenta ÚNICAMENTE un resumen estructurado de tu razonamiento y decisiones de diseño. No escribas código todavía.
>
> Debes determinar:
>
> Qué variables participan en el cálculo.
> Qué unidades debe utilizar cada variable.
> Cómo debería influir el tipo de vehículo.
> Cómo debería influir el peso de la carga.
> Cómo debería utilizarse la distancia.
> Cómo debería utilizarse el efficiency_factor.
> Qué fórmula propones para calcular las emisiones.
> Qué supuestos estás haciendo.
> Qué valores deberían considerarse inválidos.
> Qué errores debería devolver el sistema.
> Qué casos de borde deberían probarse.
> Qué información falta o es ambigua en los requisitos actuales.
>
> Si la fórmula exacta no puede determinarse con la información proporcionada, NO inventes una fórmula silenciosamente. Propón una fórmula razonable como modelo académico y marca claramente los supuestos.
>
> Finalmente, presenta:
>
> Fórmula propuesta.
> Ejemplo numérico sencillo.
> Reglas de validación.
> Casos de error.
> Decisiones arquitectónicas relevantes.
>
> No generes código todavía.

### Respuesta / resultado

Documento de análisis completo: variables con unidades (salida en kg CO₂); influencia de cada input; **fórmula modelo académico marcada como supuesto**: `CO₂_kg = EF(tipo) × distancia_km × (1 + λ·peso_tons) × efficiency_factor` con λ=0.02 y tabla de factores EF (electric=0 tank-to-wheel, diesel=0.90, hybrid=0.55); ejemplo numérico (198 kg); reglas de validación con guardarrailes; mapeo de errores 422 (sintáctico) / 400 (semántico); casos de borde; lista de información faltante; y 8 decisiones arquitectónicas (dominio puro, Protocol para proveedor de factores, DI, resultado con desglose, coeficientes centralizados, Strategy pospuesto, doble capa de validación, redondeo solo en frontera).

---

## Prompt 3 — Ejemplos de comportamiento y reglas generales

### Prompt completo

> Está correcto lo que propones, además de esto, Utiliza los siguientes ejemplos como referencia del comportamiento esperado del Carbon Tracker Service.
>
> EJEMPLO 1 — Vehículo diésel válido:
> Entrada:
> vehicle_type = "diesel"
> cargo_weight_tons = 5
> distance_km = 100
> efficiency_factor = 1.0
>
> Resultado esperado:
> El sistema debe calcular una cantidad positiva de emisiones de CO2.
>
> EJEMPLO 2 — Vehículo eléctrico:
> Entrada:
> vehicle_type = "electric"
> cargo_weight_tons = 2
> distance_km = 100
> efficiency_factor = 0.8
>
> Resultado esperado:
> El sistema debe calcular las emisiones utilizando las reglas correspondientes a un vehículo eléctrico.
>
> EJEMPLO 3 — Distancia cero:
> Entrada:
> vehicle_type = "diesel"
> cargo_weight_tons = 5
> distance_km = 0
> efficiency_factor = 1.0
>
> Resultado esperado:
> Las emisiones deberían ser 0, siempre que el resto de los parámetros sean válidos.
>
> EJEMPLO 4 — Peso negativo:
> Entrada:
> vehicle_type = "diesel"
> cargo_weight_tons = -5
> distance_km = 100
> efficiency_factor = 1.0
>
> Resultado esperado:
> La solicitud debe ser rechazada mediante un error de validación.
>
> EJEMPLO 5 — Vehículo desconocido:
> Entrada:
> vehicle_type = "spaceship"
> cargo_weight_tons = 5
> distance_km = 100
> efficiency_factor = 1.0
>
> Resultado esperado:
> La solicitud debe ser rechazada porque el tipo de vehículo no está soportado.
>
> A partir de estos ejemplos, identifica las reglas generales que debería seguir la implementación.
>
> No escribas código todavía.

### Respuesta / resultado

Se detectó que el **Ejemplo 3 contradecía mi regla propuesta** (`distance_km > 0`): el requisito manda → regla actualizada a `distance_km ≥ 0`. Se derivaron 7 reglas generales: R1 proporcionalidad multiplicativa (distancia 0 ⇒ 0 sin caso especial codificado), R2 tank-to-wheel para eléctricos (η irrelevante), R3 combustión válida ⇒ positivo, R4 validación total previa sin cortocircuito entre campos, R5 contrato estricto case-sensitive con mensajes informativos, R6 errores como parte del contrato (422/400, nunca 500), R7 determinismo/pureza. Matriz de aceptación A1–A9 trazable a tests futuros. Impacto arquitectónico: ninguno estructural.

---

## Prompt 4 — Implementación de la primera versión funcional

### Prompt completo

> Ahora implementa la primera versión funcional del Carbon Tracker Service utilizando la arquitectura que acabamos de definir.
>
> Tecnologías:
>
> * Python 3.12+
> * FastAPI
> * Pydantic
> * Pytest
>
> Requisitos:
>
> 1. Crear los modelos de entrada y salida.
> 2. Crear la lógica de negocio para calcular las emisiones.
> 3. Crear los endpoints HTTP.
> 4. Validar los datos de entrada.
> 5. Manejar tipos de vehículo no soportados.
> 6. Mantener la lógica de cálculo independiente de FastAPI.
> 7. Utilizar type hints.
> 8. Utilizar nombres descriptivos.
> 9. Mantener funciones pequeñas y con una única responsabilidad.
> 10. Evitar lógica duplicada.
> 11. Utilizar excepciones apropiadas.
> 12. Añadir documentación mínima mediante docstrings cuando aporte valor.
>
> El endpoint principal debe permitir calcular las emisiones mediante una petición HTTP.
>
> IMPORTANTE:
>
> * No pongas toda la lógica en main.py.
> * No utilices variables globales innecesarias.
> * No ocultes errores mediante try/except excesivamente amplios.
> * No añadas dependencias innecesarias.
> * Mantén la solución sencilla.
>
> Primero muestra la estructura de archivos y después proporciona el contenido de cada archivo.

### Respuesta / resultado

Implementación completa en capas: `pyproject.toml` (uv + hatchling + ruff + pytest); `domain/` puro (`errors.py`, `models.py` con `VehicleType` StrEnum y `Trip` frozen con invariantes, `emission_factors.py` Protocol+tabla ASSUMPTION, `calculator.py` fórmula centralizada y `EmissionResult` con desglose); `application/use_cases.py`; `api/` (`schemas.py`, `dependencies.py` con lru_cache, `routes.py` POST `/api/v1/emissions/calculate`, `error_handlers.py` envolvente uniforme, `main.py` app factory). README con supuestos.

Hallazgos resueltos durante la construcción: Pydantic 2.13 no soporta `strict="str"` a nivel modelo → validador explícito `reject_non_number_types`; el JSON estándar no transporta `Infinity` → test con cuerpo bruto no-estándar; migración `(str, Enum)` → `StrEnum` sugerida por ruff. Verificación: 47 tests verdes, ruff limpio, smoke test real con uvicorn+curl confirmando los 5 ejemplos del contrato (diesel→99.0 kg, electric→0.0, spaceship→422 informativo, peso negativo→422, distancia 0→200).

---

## Prompt 5 — Revisión crítica de la validación de entradas

### Prompt completo

> Revisa críticamente la implementación anterior.
>
> No quiero todavía una reescritura completa. Primero identifica problemas relacionados con la validación de entradas.
>
> Analiza específicamente:
>
> * vehicle_type vacío.
> * vehicle_type con mayúsculas/minúsculas diferentes.
> * vehicle_type no soportado.
> * cargo_weight_tons negativo.
> * cargo_weight_tons igual a cero.
> * distance_km negativo.
> * distance_km igual a cero.
> * efficiency_factor negativo.
> * efficiency_factor igual a cero.
> * valores extremadamente grandes.
> * tipos de datos incorrectos.
> * valores null/missing.
> * números NaN o infinitos si pueden llegar a la aplicación.
> * valores con demasiados decimales.
>
> Para cada problema indica:
>
> 1. Si debe aceptarse o rechazarse.
> 2. En qué capa debería validarse.
> 3. Qué error debería producirse.
> 4. Por qué esa decisión es apropiada.
>
> Después propone los cambios concretos necesarios para mejorar la implementación.

### Respuesta / resultado

Verificación empírica mediante sondas HTTP reales. Tabla completa de los 14 casos: 12 ya correctamente cubiertos. **Bug real confirmado**: `cargo_weight_tons: true` devolvía HTTP 200 (bool es subclase de int; Pydantic lax coacciona true→1.0) y el dominio también lo aceptaba — doble fallo de defensa en profundidad. Caso «demasiados decimales» presentado como decisión abierta: A) aceptar y documentar (recomendada, float64 ya limita precisión) vs B) cota estricta de 4 decimales. Hallazgo menor documentable: resultados <0.005 kg se muestran como `0.0` por redondeo aunque el dominio garantice positividad.

Cambios propuestos: rechazo explícito de bool en schemas y dominio, tests nuevos (incluidas fronteras superiores exactas), actualización de README. Verificado también: entero gigante (400 dígitos) → 422 limpio; `1e400` → inf → rechazado por `allow_inf_nan=False`.

---

## Prompt 6 — Revisión de diseño y mantenibilidad

### Prompt completo

> Antes de esto, Realiza una revisión de la implementación enfocada exclusivamente en diseño y mantenibilidad.
>
> Evalúa:
>
> * Single Responsibility Principle.
> * Open/Closed Principle.
> * Dependency Inversion.
> * Separation of Concerns.
> * Acoplamiento entre FastAPI y la lógica de negocio.
> * Facilidad para añadir un nuevo tipo de vehículo.
> * Duplicación de código.
> * Tamaño y responsabilidad de las funciones.
> * Facilidad para escribir tests unitarios.
>
> Identifica primero los problemas encontrados.
>
> Después propone una versión mejorada de la arquitectura.
>
> Si consideras que utilizar Strategy Pattern para diesel, electric e hybrid mejora realmente el diseño, muéstralo. Si consideras que sería overengineering para este microservicio, explica por qué y conserva una solución más sencilla.
>
> No introduzcas patrones de diseño únicamente para hacer el proyecto más complejo.

### Respuesta / resultado

Problemas identificados: P1 duplicación real en tests (`build_trip()` y `VALID_DIESEL_PAYLOAD` copiados entre archivos); P2 repetición estructural en error_handlers; P3 configuración incompleta fallaba en primera petición en vez de en arranque; P4 DIP parcial consciente (use case → calculador concreto, tradeoff documentado); P5 menores (mezcla enum+constantes+VO+validadores en models.py; inconsistencia idiomática ES/EN).

Violaciones aparentes defendidas como correctas: SRP/OCP cumplidos vía registro de datos sin ramas; acoplamiento FastAPI-negocio correcto (dirección api→dominio única); funciones ≤12 líneas; testabilidad buena.

**Verdicto Strategy Pattern: NO — overengineering hoy** (misma expresión algebraica para los 3 tipos, solo difiere EF; OCP ya satisfecho con dict+Protocol). Trigger objetivo definido para extraerlo en el futuro: divergencia estructural de fórmulas (well-to-wheel eléctrico, híbrido con doble consumo). Refactor ligero propuesto: fixtures compartidas, fábrica `_json_error`, fail-fast `assert_covers_all_types()`, convenciones en README.

---

## Prompt 7 — Aprobación del paquete combinado

### Prompt completo

> Sí

### Respuesta / resultado

Ejecución del paquete aprobado (fixes de validación + refactors de diseño): rechazo de bool en `schemas.py` (`reject_non_number_types`) y en dominio (`_reject_non_numeric`, que además elimina fuga de TypeError crudo con strings); fixtures compartidas `build_trip`, `endpoint`, `diesel_payload` en conftests; fábrica `_json_error()` + `_domain_error_response()` en handlers; `assert_covers_all_types()` invocado al construir el proveedor (fail-fast en arranque); README actualizado con política de booleanos/overflow/decimales y sección Convenciones (Strategy pospuesto, DIP parcial consciente, idiomas).

Verificación: 69 tests (+22), ruff limpio, smoke test confirmando `true`→422, frontera exacta peso=100/distancia=10000/η=10→200 y comportamiento normal intacto (99.0 kg).

---

## Prompt 8 — Suite completa de pruebas unitarias

### Prompt completo

> Genera una suite completa de pruebas unitarias utilizando Pytest para el Carbon Tracker Service.
>
> Objetivo: alcanzar al menos un 90% de cobertura sobre la lógica de negocio.
>
> Las pruebas deben cubrir como mínimo:
>
> CASOS VÁLIDOS:
>
> * Vehículo diésel.
> * Vehículo eléctrico.
> * Vehículo híbrido.
> * Diferentes pesos de carga.
> * Diferentes distancias.
> * Diferentes factores de eficiencia.
> * Distancia cero si es válida.
>
> CASOS INVÁLIDOS:
>
> * Peso negativo.
> * Distancia negativa.
> * Factor de eficiencia negativo.
> * Tipo de vehículo inexistente.
> * Tipo de vehículo vacío.
> * Campos obligatorios ausentes.
> * Tipos de datos incorrectos.
> * Valores extremadamente grandes cuando corresponda.
>
> CASOS DE BORDE:
>
> * Peso igual a cero.
> * Distancia igual a cero.
> * Efficiency factor igual a cero.
> * Valores decimales.
> * Valores muy pequeños.
> * Valores muy grandes.
>
> REQUISITOS:
>
> * Usa nombres de tests descriptivos.
> * Organiza las pruebas por comportamiento.
> * Utiliza parametrización de Pytest cuando reduzca duplicación.
> * No pruebes detalles internos innecesarios.
> * Prioriza comportamiento observable.
> * Explica qué requisito valida cada grupo de tests.
>
> Después de generar los tests, indica qué partes de la lógica todavía podrían quedar sin cobertura.

### Respuesta / resultado

Cobertura medida al inicio (97%) para dirigir el esfuerzo; resultado final **100% en todo el paquete** con 135 tests (+66). Nuevos grupos organizados por comportamiento: `TestValidVehiclesByType` (totales exactos diesel 99.0/hybrid 60.5), `TestInputValueGrids` (rejillas parametrizadas peso/distancia/η contra fórmula cerrada), `TestBoundaryValues` (máximo permitido = 270 000 kg exactos, valores mínimos 1e-9, decimales múltiples, peso 0 sin penalización), `tests/unit/api/test_schemas.py` (campos ausentes ×4, tipos incorrectos, enum vacío/nulo/numérico, NaN/inf, fronteras, redondeo de `from_result`), `test_error_handlers.py` (invocación directa async de handlers, cubre red de seguridad DOMAIN_ERROR inalcanzable vía HTTP).

**Hallazgo que modificó código de producción:** `Trip(vehicle_type="spaceship")` atravesaba el dominio sin rechazo → añadido `_validate_vehicle_type`. Correcciones durante la ejecución: expectativas de eficiencia recalculadas (olvidaba multiplicador de carga: 49.5/148.5/990.0), comparación contra `exception_handlers.values()` (claves vs valores), orden de imports y línea larga según ruff.

Honestidad sobre cobertura restante: combinatoria completa (candidata a Hypothesis), JSON truncado por bytes, concurrencia real del caché, handler DOMAIN_ERROR inalcanzable por diseño, contrato OpenAPI sin aserciones.

---

## Prompt 9 — Pruebas de endpoints FastAPI

### Prompt completo

> Además de los tests unitarios de la lógica de negocio, crea pruebas para los endpoints de FastAPI.
>
> Utiliza pytest y el mecanismo de testing apropiado para FastAPI.
>
> Verifica:
>
> 1. Request válida → HTTP 200.
> 2. Request con datos inválidos → HTTP 4xx apropiado.
> 3. Tipo de vehículo inválido.
> 4. Campos obligatorios ausentes.
> 5. Valores negativos.
> 6. Formato incorrecto del JSON.
> 7. Response con la estructura esperada.
> 8. Tipo de datos correcto en la respuesta.
> 9. Que los errores tengan respuestas consistentes.
>
> Mantén separadas las pruebas de API de las pruebas puramente unitarias de la lógica de cálculo.
>
> Explica brevemente qué diferencia existe entre ambos tipos de pruebas.

### Respuesta / resultado

Mapeo de los 9 puntos contra la suite existente y archivo nuevo `test_endpoint_responses.py` solo con lo faltante (sin duplicar): happy path con content-type JSON; estructura exacta de respuesta (claves top-level y breakdown, sin campo error fantasma); tipos correctos de cada campo; JSON malformado (truncado, cuerpo vacío, array no-objeto) → 422 uniforme; consistencia de la envolvente `{code,message,details}` entre 4 escenarios distintos y entre JSON roto vs dato inválido. Mecanismo: `TestClient` sobre fixtures compartidas del conftest.

Explicación incluida: pruebas unitarias = lógica aislada del entorno (rápidas, localización quirúrgica, fakes); pruebas de API = contrato observable desde la frontera HTTP (serialización, validación, DI, códigos de estado); un fallo de integración con unitarias verdes apunta a cableado, no a algoritmo. Resultado: 143 tests, ruff limpio.

---

## Prompt 10 — Creación de esta bitácora

### Prompt completo

> Necesito que crees una bitácora de prompts en el proyecto (MD) en él pondrás todos los prompts que realicé, y un resumen de tus respuestas o código generado. Los prompts deben estar completos por favor.

### Respuesta / resultado

Este documento: 10 entradas cronológicas con prompts íntegros y resumen de resultados, más índice navegable.

---

## Prompt 11 — Code review independiente (Senior SWE)

### Prompt completo

> Actúa como un Senior Software Engineer realizando un code review de un microservicio que calcula emisiones de CO2.
>
> IMPORTANTE:
> Esta es una revisión independiente. No asumas que el código es correcto simplemente porque fue generado previamente por otro LLM.
>
> Revisa críticamente:
>
> ### Correctitud
>
> * Fórmula de cálculo.
> * Unidades.
> * Manejo de los diferentes vehículos.
> * Casos de borde.
> * Manejo de errores.
>
> ### Seguridad
>
> * Validación de inputs.
> * Posibles inputs maliciosos.
> * Denial of Service mediante valores extremos.
> * Exposición innecesaria de información.
> * Manejo de excepciones.
> * Validación de tipos.
> * Dependencias y configuración.
>
> ### Rendimiento
>
> * Complejidad innecesaria.
> * Operaciones costosas.
> * Uso innecesario de memoria.
> * Posibles problemas bajo múltiples requests concurrentes.
>
> ### Arquitectura
>
> * SOLID.
> * Separation of Concerns.
> * Acoplamiento.
> * Testabilidad.
> * Escalabilidad.
> * Facilidad para añadir nuevos tipos de vehículos.
>
> ### Calidad
>
> * Legibilidad.
> * Naming.
> * Type hints.
> * Duplicación.
> * Manejo de errores.
> * Código muerto.
> * Código innecesariamente complejo.
>
> Para cada problema encontrado proporciona:
>
> * Severidad: CRITICAL / HIGH / MEDIUM / LOW.
> * Archivo y ubicación.
> * Problema.
> * Por qué es un problema.
> * Recomendación concreta.
>
> No reescribas todo el proyecto todavía. Primero realiza únicamente el review.

### Respuesta / resultado

Review completo del proyecto post-implementación (143 tests, 538 LOC fuente). Se identificaron **10 problemas** priorizados por severidad:

| # | Problema | Severidad | Archivo |
|---|---|---|---|
| 1 | `assert_covers_all_types()` solo se ejecutaba lazy (primera petición), no al arranque real | CRITICAL | `dependencies.py` |
| 2 | Sin logging en producción (routes, errors, startup) | HIGH | `routes.py`, `error_handlers.py`, `main.py` |
| 3 | Sin rate limiting | HIGH | `routes.py` |
| 4 | `EmissionCalculator.__init__` no valida el tipo del provider en runtime | MEDIUM | `calculator.py` |
| 5 | Tabla de factores es `dict` mutable después de init | MEDIUM | `emission_factors.py` |
| 6 | Mensaje confuso para `efficiency_factor=0` ("greater than 0") | LOW | `models.py` |
| 7 | Función síncrona bloquea event loop | LOW | `calculator.py` |
| 8 | `_reject_non_numeric` no valida `int/float` explícitamente | LOW | `models.py` |
| 9 | Sin Dockerfile | LOW | raíz |
| 10 | Sin `py.typed` marker | LOW | `src/` |

Se valoraron positivamente: fórmula correcta, defensa en profundidad completa, Clean Architecture bien ejecutada, suite de tests exhaustiva (143 tests), naming consistente, redondeo solo en frontera HTTP.

---

## Prompt 12 — Corrección de problemas del review

### Prompt completo

> Ahora corrige únicamente los problemas identificados durante el code review anterior.
>
> REQUISITOS:
>
> * No cambies comportamiento que ya sea correcto.
> * No introduzcas patrones innecesarios.
> * Mantén la arquitectura modular.
> * Conserva la compatibilidad con los tests existentes siempre que sea posible.
> * Si modificas un comportamiento, explica por qué.
> * No elimines tests para hacer que la suite pase.
> * Añade nuevos tests cuando una corrección requiera cubrir un nuevo escenario.
>
> Para cada cambio realizado, indica:
>
> 1. Problema original.
> 2. Cambio realizado.
> 3. Motivo.
> 4. Test que demuestra que el problema quedó solucionado.
>
> Después muestra el código actualizado de los archivos modificados.

### Respuesta / resultado

Se corrigieron **8 de 10 problemas** (2 diferidos intencionalmente):

| # | Corrección | Archivos modificados | Tests nuevos |
|---|---|---|---|
| 1 | `_validate_emission_factors_at_startup()` en `main.py` para fail-fast real | `main.py` | 2 tests (startup validation) |
| 2 | Logging en routes (request + resultado), error handlers (warning), y startup (info) | `main.py`, `routes.py`, `error_handlers.py` | 0 (no cambia comportamiento) |
| 4 | Runtime type check: `callable(getattr(factor_provider, "get_base_emission_factor", None))` | `domain/calculator.py` | 1 test (provider inválido) |
| 5 | `dict` → `MappingProxyType` para inmutabilidad de tabla de factores | `domain/emission_factors.py` | 2 tests (custom + default immutable) |
| 6 | Mensaje: `"greater than 0 and at most 10"` → `"in the range (0, 10]"` | `domain/models.py` | 0 (test existente ya cubre) |
| 8 | Check explícito `isinstance(value, (int, float))` tras el filtro str/bool | `domain/models.py` | 9 tests (dict, list, bytes × 3 campos) |
| 9 | Dockerfile multi-stage (python:3.12-slim + uv + usuario no-root) | `Dockerfile` (nuevo) | N/A |
| 10 | `py.typed` marker para type checkers | `src/carbon_tracker/py.typed` (nuevo) | N/A |

**Diferidos intencionalmente:**
- #3 (rate limiting): depende de infraestructura externa, no del microservicio.
- #7 (sync event loop): O(1) aritmética pura, FastAPI ejecuta en thread pool, inocuo actualmente.

**Resultado:** 157 tests pasan (143 originales + 14 nuevos), ruff limpio, cero regresiones.

---

## Prompt 13 — Auditoría final del proyecto

### Prompt completo

> Excelente, por último, realiza una auditoría final del Carbon Tracker Service después de todas las modificaciones.
>
> Evalúa el proyecto de 0 a 10 en:
>
> 1. Correctitud funcional.
> 2. Validación de entradas.
> 3. Manejo de errores.
> 4. Modularidad.
> 5. Principios SOLID.
> 6. Testabilidad.
> 7. Cobertura de pruebas.
> 8. Seguridad.
> 9. Rendimiento.
> 10. Legibilidad.
>
> Para cada categoría:
>
> * Da una puntuación.
> * Justifica brevemente.
> * Identifica cualquier problema restante.
>
> Después responde:
>
> 1. ¿Qué partes del código fueron generadas inicialmente por el LLM?
> 2. ¿Qué partes fueron modificadas mediante refinamiento iterativo?
> 3. ¿Qué problemas fueron detectados durante el code review?
> 4. ¿Qué problemas fueron solucionados?
> 5. ¿Qué riesgos permanecen?
> 6. ¿Qué decisiones requirieron criterio humano en lugar de aceptar directamente la sugerencia del LLM?
>
> Finalmente, proporciona una lista de comprobación para verificar que el proyecto está listo para ser entregado.

### Respuesta / resultado

**Puntuaciones:**

| Categoría | Puntuación |
|---|---|
| 1. Correctitud funcional | 9/10 |
| 2. Validación de entradas | 9.5/10 |
| 3. Manejo de errores | 9/10 |
| 4. Modularidad | 9.5/10 |
| 5. Principios SOLID | 9/10 |
| 6. Testabilidad | 9.5/10 |
| 7. Cobertura de pruebas | 8.5/10 |
| 8. Seguridad | 8/10 |
| 9. Rendimiento | 9/10 |
| 10. Legibilidad | 9/10 |
| **Global** | **8.95/10** |

**Trazabilidad del proceso:**
- Todo el código fue generado inicialmente por un LLM (modelo `ox-alpha`).
- El refinamiento iterativo se hizo en 3 fases: generación → code review (modelo `big-pickle`) → correcciones.
- 10 problemas detectados durante el review (1 CRITICAL, 2 HIGH, 2 MEDIUM, 5 LOW).
- 8 corregidos con código, 2 diferidos intencionalmente (rate limiting y sync event loop).
- Riesgos permanentes: factores de emisión no certificados, sin rate limiting, sin CI/CD, sin coverage threshold configurado.
- Decisiones que requirieron criterio humano: valores de EF, rate limiting como infra, CORS, semántica de efficiency_factor, tank-to-wheel, configuración del Dockerfile.

---

## Estado final del proyecto tras estas iteraciones

- **Código**: microservicio FastAPI en capas (dominio puro → aplicación → API), endpoint `POST /api/v1/emissions/calculate`, errores uniformes, fail-fast en arranque, logging en routes/errors/startup, inmutabilidad de tabla de factores, runtime type check del provider, Dockerfile multi-stage, py.typed marker.
- **Calidad**: 157 tests (unitarios + integración), ruff limpio, auditoría global 8.95/10.
- **Proceso**: generación inicial (ox-alpha) → code review independiente (big-pickle) → correcciones iterativas → auditoría final. Los 143 tests originales no fueron modificados; 14 tests nuevos validan las correcciones.
- **Pendiente de negocio**: fórmula definitiva (activa la provisional marcada `ASSUMPTION`), semántica oficial de `efficiency_factor`, valores certificados de factores de emisión.
- **Pendiente de operaciones**: rate limiting (en gateway), CI/CD pipeline, coverage threshold (`pytest-cov --fail-under=90`), CORS si aplica.
