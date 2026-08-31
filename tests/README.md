# Pruebas — ms-plan-nutricional

Suite de **pruebas unitarias** del BC3 – Planificación Nutricional, aplicando el
taller de Unit Tests al caso de estudio del proyecto final.

**143 tests · 82 % de cobertura · sin base de datos.**

---

## 1. Qué se prueba y qué no

| Capa | ¿Se prueba? | Por qué |
|---|---|---|
| `domain/` | **Sí** — 115 tests | Modelo puro, sin I/O: se prueba con objetos reales |
| `application/use_cases/` | **Sí** — 28 tests | Orquestación: los repositorios se sustituyen por mocks |
| `infrastructure/` | No | Requiere PostgreSQL — fuera del alcance de este avance |
| `presentation/` | No | Serían pruebas de integración de la API — fuera del alcance |

Las dos últimas están excluidas de la medición de cobertura en `pyproject.toml`
(`[tool.coverage.run] omit`), para que el porcentaje refleje lo que realmente se
probó y no se diluya con capas no cubiertas.

---

## 2. Cómo ejecutar

```bash
# Instalar dependencias (incluye el grupo dev: pytest, pytest-asyncio, pytest-cov)
uv sync

# Toda la suite
uv run pytest -q

# Solo dominio / solo casos de uso
uv run pytest tests/unit/domain -q
uv run pytest tests/unit/application -q

# Un archivo concreto, con detalle
uv run pytest tests/unit/domain/test_plan_nutricional.py -v

# Filtrar por nombre
uv run pytest -k "duplicado" -v
```

> **No hace falta levantar PostgreSQL.** Si la suite pasa con la base de datos
> apagada, es la prueba de que los dobles aíslan correctamente el dominio de la
> infraestructura.

### Cobertura

```bash
uv run pytest --cov --cov-report=term-missing --cov-report=html
```

El reporte HTML queda en `htmlcov/index.html`:

```powershell
Start-Process .\htmlcov\index.html    # Windows
```

```bash
open htmlcov/index.html               # macOS
xdg-open htmlcov/index.html           # Linux
```

---

## 3. Estructura

La carpeta espeja la arquitectura de `src/plan_nutricional/`, de modo que para
cada módulo de producción hay un archivo de test en la misma posición relativa.

```
tests/
├── conftest.py                 # fixtures compartidas (builders + mocks)
└── unit/
    ├── domain/                 # espeja src/plan_nutricional/domain/model/
    │   ├── test_value_objects.py
    │   ├── test_plan_nutricional.py
    │   ├── test_plan_dia.py
    │   ├── test_tiempo_comida.py
    │   ├── test_receta_catalogo.py
    │   └── test_plantilla_plan.py
    └── application/            # espeja src/plan_nutricional/application/use_cases/
        ├── test_crear_plan.py
        ├── test_agregar_dia.py
        ├── test_cambiar_estado_plan.py
        ├── test_agregar_receta_desde_catalogo.py
        └── test_crear_plan_desde_plantilla.py
```

`conftest.py` centraliza lo que se repetiría en cada test:

- **Builders de dominio** — `construir_plan()`, `construir_plantilla()`,
  `necesidad`, `receta_catalogo`. Evitan repetir el armado de un plan válido en
  cada prueba y permiten variar solo lo que interesa:
  `construir_plan(dias_duracion=30, dias=[1, 2], estado=EstadoPlan.FINALIZADO)`.
- **Mocks de los puertos** — `plan_repo_mock`, `catalogo_repo_mock`,
  `plantilla_repo_mock`.

---

## 4. Qué es un mock y por qué se usa aquí

### El problema

Los casos de uso reciben su repositorio por **inyección de dependencias**:

```python
class AgregarDiaUseCase:
    def __init__(self, repo: PlanNutricionalRepository) -> None:
        self._repo = repo
```

El repositorio real (`infrastructure/persistence/plan_repository_impl.py`) habla
con PostgreSQL. Usarlo en una prueba unitaria obligaría a levantar una base de
datos: el test sería lento, frágil y dependería del entorno.

### La solución

Un **mock** es un objeto falso que ocupa el lugar de esa dependencia. Permite dos
cosas que un objeto real no permite:

```python
# (a) Controlar qué devuelve la dependencia
plan_repo_mock.obtener_por_id.return_value = plan

# (b) Verificar cómo se la usó
plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
plan_repo_mock.guardar.assert_awaited_once_with(plan)
```

Se usa `AsyncMock`, la variante para dependencias asíncronas (sus métodos se
pueden `await`), porque los tres puertos del microservicio son 100 % `async`.

### Por qué `spec=` es obligatorio

```python
AsyncMock(spec=PlanNutricionalRepository)
```

`spec=` obliga al mock a exponer **exactamente** los métodos que declara el
puerto. Sin él, un mock acepta cualquier llamada: escribir `repo.obtner_por_id()`
devolvería otro mock y el test pasaría en verde ocultando el error. El test
`test_el_mock_con_spec_rechaza_metodos_que_no_existen_en_el_puerto` demuestra
esta protección.

### La regla del camino de error

Todo test que comprueba un error debe afirmar además que **no se persistió nada**:

```python
with pytest.raises(PlanNoEncontradoError):
    await caso_de_uso.ejecutar(cmd)

plan_repo_mock.guardar.assert_not_awaited()
```

Sin esa línea, el test demostraría que se lanza la excepción, pero no que la base
de datos quedó intacta. Es la diferencia entre "falla" y "falla limpiamente".

### Ejemplo completo

De `tests/unit/application/test_agregar_dia.py`:

```python
async def test_agregar_dia_valido_devuelve_el_dia_y_persiste_el_plan(
    plan_repo_mock, construir_plan
):
    # Arrange — el mock devuelve el plan que decidimos, sin tocar la base de datos
    plan = construir_plan(dias_duracion=15)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarDiaUseCase(plan_repo_mock)

    # Act
    dia = await caso_de_uso.ejecutar(AgregarDiaCommand(plan_id=plan.id, numero_dia=3))

    # Assert — se verifica el resultado y también CÓMO se usó la dependencia
    assert dia.numero_dia == 3
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)
```

### Cheatsheet

| Necesito… | Cómo |
|---|---|
| Que devuelva un valor fijo | `mock.metodo.return_value = plan` |
| Que devuelva "no existe" | `mock.metodo.return_value = None` |
| Un valor distinto por llamada | `mock.metodo.side_effect = [a, b, None]` |
| Que lance una excepción | `mock.metodo.side_effect = ErrorDeDominio(...)` |
| Verificar una llamada exacta | `mock.metodo.assert_awaited_once_with(id)` |
| Verificar que NO se llamó | `mock.metodo.assert_not_awaited()` |
| Contar llamadas | `mock.metodo.await_count == 2` |
| Verificar varias llamadas | `mock.metodo.assert_has_awaits([call(a), call(b)])` |
| Inspeccionar el argumento recibido | `mock.guardar.await_args.args[0]` |

> En `AsyncMock` se usan las variantes `*_awaited_*`, no `assert_called_once_with`.

Los casos con **varios repositorios inyectados** permiten además verificar el
**corto-circuito**: si el plan no existe, el catálogo ni siquiera debería
consultarse (`catalogo_repo_mock.obtener_por_id.assert_not_awaited()`).

---

## 5. Patrón AAA y convención de nombres

Cada test se estructura en tres bloques explícitos:

- **Arrange** — preparar los datos y los dobles.
- **Act** — ejecutar la acción bajo prueba.
- **Assert** — comprobar el resultado.

Cuando Act y Assert coinciden en la misma línea (`pytest.raises`), se fusionan en
`# Act / Assert`.

Los nombres siguen `test_<accion>_<condicion>_<resultado_esperado>`, en español,
de modo que la salida de pytest se lea como una especificación:

```python
def test_agregar_dia_fuera_de_duracion_lanza_error(construir_plan):
    # Arrange
    plan = construir_plan(dias_duracion=15)

    # Act / Assert
    with pytest.raises(DiaFueraDeDuracionError):
        plan.agregar_dia(16)
```

Las variantes del mismo comportamiento se agrupan con `@pytest.mark.parametrize`
en lugar de duplicar el test. Por eso `test_plan_nutricional.py` cubre la matriz
completa de transiciones de estado (7 combinaciones inválidas) en un solo test.

---

## 6. Inventario de la suite

| Archivo | Tests | Qué cubre |
|---|---|---|
| `unit/domain/test_plan_nutricional.py` | 42 | Aggregate Root: duración, duplicados, copias defensivas, ciclo de vida |
| `unit/domain/test_value_objects.py` | 30 | Los 4 VO: validaciones, inmutabilidad, igualdad por valor |
| `unit/domain/test_plantilla_plan.py` | 16 | Plantilla: días, tiempos, recetas del catálogo |
| `unit/domain/test_tiempo_comida.py` | 10 | Recetas duplicadas (case-insensitive), eliminación |
| `unit/domain/test_receta_catalogo.py` | 9 | Catálogo: creación, actualización, activar/desactivar |
| `unit/domain/test_plan_dia.py` | 8 | Tiempos de comida duplicados y no encontrados |
| `unit/application/test_crear_plan.py` | 6 | Creación y validaciones que abortan la persistencia |
| `unit/application/test_agregar_receta_desde_catalogo.py` | 6 | Dos mocks, tres ramas de error, porción por defecto |
| `unit/application/test_crear_plan_desde_plantilla.py` | 6 | Tres mocks, `side_effect`, `assert_has_awaits` |
| `unit/application/test_agregar_dia.py` | 5 | Patrón de referencia de mocking |
| `unit/application/test_cambiar_estado_plan.py` | 5 | Transiciones inválidas sin persistencia parcial |
| **Total** | **143** | |

---

## 7. Cobertura

Resultado de `uv run pytest --cov --cov-report=term-missing`:

| Módulo | Cobertura |
|---|---|
| `domain/model/value_objects.py` | 100 % |
| `domain/model/receta_catalogo.py` | 100 % |
| `domain/model/plan_nutricional.py` | 98 % |
| `domain/model/tiempo_comida.py` | 98 % |
| `domain/model/plan_dia.py` | 97 % |
| `domain/model/plantilla_plan.py` | 87 % |
| Los 5 casos de uso probados | 100 % |
| **Total del alcance medido** | **82 %** |

Dos decisiones sobre la configuración (`pyproject.toml`):

- **No hay `fail_under`.** La cobertura se mide y se reporta, pero no hace fallar
  la suite. Es coherente con un avance del taller que no pretende ser exhaustivo:
  un umbral obligaría a escribir tests de relleno para pasar el corte.
- **`htmlcov/` y `.coverage` están en `.gitignore`.** Son artefactos regenerables
  con un comando; no se versionan. Para presentar evidencia basta una captura del
  reporte HTML o del resumen en terminal.

---

## 8. Hallazgo documentado

Al enumerar las ramas de los casos de uso apareció una **asimetría real de
comportamiento** entre dos de ellos:

| Caso de uso | ¿Verifica `receta_catalogo.activa`? |
|---|---|
| `agregar_receta_desde_catalogo.py` | Sí — lanza `RecetaCatalogoInactivaError` |
| `crear_plan_desde_plantilla.py` | **No** — copia la receta igualmente |

Es decir: una receta desactivada no se puede añadir a mano a un plan, pero sí
entra si el plan se genera desde una plantilla.

**No se modificó código de producción.** En su lugar se escribió el test
`test_una_receta_inactiva_del_catalogo_si_se_copia_al_plan`, que fija el
comportamiento actual y documenta la inconsistencia en su docstring. Si en el
futuro se decide unificar el criterio, ese test fallará y habrá que actualizarlo
de forma deliberada — que es exactamente lo que debe hacer una prueba de
regresión.

---

## 9. Entorno de pruebas para IA

En `.claude/` hay dos piezas complementarias:

| Archivo | Qué es |
|---|---|
| `.claude/agents/test-writer.md` | Un **subagente** especializado: tiene sus propias herramientas, reglas y prohibiciones |
| `.claude/skills/testing-plan-nutricional/SKILL.md` | Una **skill**: las convenciones del proyecto, consultables por cualquiera |

La diferencia: el agente es *quién* hace el trabajo; la skill es *cómo* se hace.
El agente, en el paso 2 de su flujo, consulta la skill — así el conocimiento vive
en un solo sitio y no se duplica.

Lo que hace de esto un **entorno validado**: el flujo de trabajo del agente le
obliga a ejecutar `uv run pytest` y a reportar la cobertura antes de terminar, y
le prohíbe modificar código de `src/` para hacer pasar un test. Ningún test
generado por IA se da por bueno sin haberse ejecutado.

```
# Cargar las convenciones en la conversación actual
/testing-plan-nutricional

# Delegar en el subagente (parte de cero, ejecuta pytest y reporta)
"usa el test-writer para cubrir eliminar_dia.py"
```
