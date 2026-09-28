# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

`ms-plan-nutricional` — microservicio del BC3 (Planificación Nutricional) del sistema NUR-TRICENTER. FastAPI + SQLAlchemy async + PostgreSQL, Python >= 3.12, gestionado con **uv** (no pip, no poetry).

La documentación del proyecto está en español y los nombres de test también. Mantén ese idioma.

## Comandos

```bash
uv sync                                              # instalar (incluye grupo dev)

docker compose -f ms-plan-nutricional-docker-compose.yml up -d   # solo la BD
uv run fastapi dev main.py                           # API en el host → :8000, docs en /docs

uv run pytest -q                                     # suite completa
uv run pytest tests/unit -q                          # unitarias (no necesitan BD)
uv run pytest -m integration -v                      # integración (necesita BD)
uv run pytest tests/unit/domain/test_plan_nutricional.py::test_X -v   # un test
uv run pytest -k "duplicado" -v                      # filtrar por nombre
```

Cobertura — hay **dos** mediciones y no son intercambiables:

```bash
# OFICIAL (requisito del taller, >= 80 %): capa unitaria, sin BD. Da ~84 %.
uv run pytest tests/unit --cov --cov-report=term-missing \
    --cov-report=html:htmlcov-unit --cov-report=xml:coverage-unit.xml

# Suite completa con PostgreSQL levantado. Da ~89 %.
uv run pytest --cov --cov-report=term-missing --cov-report=html:htmlcov
```

No hay linter ni formateador configurados.

## Trampas del entorno

- **La BD escucha en el puerto 5434**, no en el 5432 — se eligió para no chocar con otros microservicios del diplomado. El default de `Settings.database_url` ya lo refleja.
- **La API no está dockerizada**: el compose levanta solo PostgreSQL; la API corre en el host.
- **Cobertura en 0 %** → falta la instalación editable: `uv sync`.
- **`fail_under = 80` aplica a cualquier invocación con `--cov`**, así que medir una subcarpeta suelta (`tests/unit/domain --cov`) falla aunque sus tests pasen: el denominador sigue siendo el paquete entero. La medición oficial es `tests/unit` completo.
- **Al regenerar `htmlcov-unit/`** hay que borrar el `htmlcov-unit/.gitignore` que coverage.py recrea con `*`; si no, la evidencia queda invisible para git.

## Arquitectura

Clean Architecture + DDD + CQRS ligero. Dependencias hacia adentro: `presentation → application → domain`. El dominio es Python puro, sin FastAPI ni SQLAlchemy.

```
src/plan_nutricional/
├── domain/          model/ (3 Aggregate Roots + entidades + VOs + enums), exceptions/, repositories/ (puertos ABC), gateways/
├── application/     commands/ y queries/ (dataclasses frozen), use_cases/ (una clase por caso de uso)
├── infrastructure/  persistence/ (ORM + impl. de los 3 repos), config/settings.py, gateways/ (mock de pacientes)
└── presentation/    api/routers/ (3), api/schemas/ (Pydantic + mappers), exception_handlers.py, main.py
```

Tres Aggregate Roots: `PlanNutricional` (el principal, con ciclo de vida), `RecetaCatalogo` y `PlantillaPlan`. Las invariantes se protegen **dentro** del agregado, nunca en el caso de uso.

**Forma canónica de un caso de uso** — casi todos son idénticos:

```python
plan = await self._repo.obtener_por_id(cmd.plan_id)
if plan is None:
    raise PlanNoEncontradoError(cmd.plan_id)
plan.metodo_de_dominio(...)          # aquí se lanzan las excepciones de negocio
await self._repo.guardar(plan)
```

**No hay contenedor de DI.** Cada router define sus propias funciones `_get_repo` / `_get_catalogo_repo` / `_get_plantilla_repo` con `Depends(get_db_session)`. Esas funciones **anotan el puerto ABC del dominio, no la implementación** — es lo que sostiene la inversión de dependencias, y hay un test unitario que lo vigila. Los tres routers comparten una única hoja: `get_db_session`, que es también el punto donde las pruebas de integración inyectan su sesión.

**Unidad de trabajo por request**: `get_db_session` hace `commit` al salir y `rollback` si hay excepción.

**Errores → HTTP**: `register_exception_handlers(app)` registra 20 manejadores que devuelven `{"detail": ..., "tipo": "<CODIGO>"}`. 404 para `*NoEncontrado*`, 409 para `*Duplicado*` / `PlanNoModificable` / `TransicionEstadoInvalida` / `RecetaCatalogoInactiva`, 422 para `*FueraDeDuracion*` y `ValueError` genérico. Si añades una excepción de dominio, añade su manejador: hay un test que lo exige.

## Invariantes de negocio que conviene saber de memoria

- `DuracionPlan` solo admite **15 o 30 días**.
- `1 <= numero_dia <= duracion.dias`.
- Transiciones de estado: `ACTIVO → {FINALIZADO, CANCELADO}`; ambos son terminales.
- Un plan que no está `ACTIVO` rechaza cualquier modificación con `PlanNoModificableError`.
- `PlantillaPlan` **no** tiene ciclo de vida: siempre es editable.
- Recetas duplicadas se detectan **ignorando mayúsculas**.
- `plan.dias`, `dia.tiempos_comida` y `tiempo.recetas` devuelven **copias defensivas**.
- La factoría `crear()` valida; el constructor `__init__` (rehidratación desde el repositorio) **no**. Es deliberado.

## Testing

Antes de escribir cualquier test, carga la skill correspondiente: `testing-plan-nutricional` (unitarias) o `integration-testing-plan-nutricional` (integración). Definen las convenciones exactas; esto es solo el resumen.

- **AAA** con comentarios `# Arrange` / `# Act` / `# Assert`. Se fusionan en `# Act / Assert` cuando coinciden en la línea del `pytest.raises`.
- Nombres en español: `test_<accion>_<condicion>_<resultado_esperado>`.
- `asyncio_mode = "auto"`: los tests `async def` **no** llevan decorador.
- Dobles: **siempre** `AsyncMock(spec=<PuertoABC>)`. Sin `spec`, un método mal escrito devuelve otro mock y el test pasa en verde.
- Usa `assert_awaited_once_with`, nunca `assert_called_once_with`.
- Cada rama de error cierra con `repo.guardar.assert_not_awaited()`.
- Fechas fijas (`date(2026, 1, 1)`), nunca `date.today()`.
- Reutiliza las fixtures de `tests/conftest.py`: `construir_plan`, `construir_plantilla`, `necesidad`, `receta_catalogo`, `plan_repo_mock`, `catalogo_repo_mock`, `plantilla_repo_mock`.

**Dónde va cada test** — lo decide el **I/O**, no la capa:

| Qué | Dónde |
|---|---|
| Dominio, casos de uso | `tests/unit/domain/`, `tests/unit/application/` |
| Mappers, tabla excepción→HTTP, composición de la app | `tests/unit/presentation/` |
| Gateways mock | `tests/unit/infrastructure/` |
| Cuerpos de endpoint, SQL de repositorios | `tests/integration/` |

Prohibido en `tests/unit/`: doblar `AsyncSession`, simular resultados de SQLAlchemy, levantar un cliente HTTP.

**Reglas duras de `tests/integration/`**: cero mocks; ningún test asume BD vacía; nada de `TRUNCATE`/`DELETE`/`DROP`; el aislamiento es una transacción reversible con `join_transaction_mode="create_savepoint"` sobre la fixture `cliente`. `tests/integration/test_convenciones_del_entorno.py` es un **guardián** de 13 tests que verifica todo esto por análisis estático — nunca lo relajes para que pase un test tuyo.

Si cambias un endpoint, actualiza también `postman/ms-plan-nutricional.postman_collection.json`.

## Restricciones

- **No modifiques `src/` para hacer pasar un test.** Si un test revela un bug o una asimetría, escribe un test que documente el comportamiento actual y dilo.
- No uses `# pragma: no cover` para esquivar cobertura, ni bajes `fail_under`.
- Los subagentes `test-writer` e `integration-test-writer` tienen alcances que no se solapan; respétalos.
