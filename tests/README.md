# Pruebas — ms-plan-nutricional

Suite de pruebas del BC3 – Planificación Nutricional. Recoge tres talleres
aplicados al caso de estudio del proyecto final:

- **Taller de Unit Tests** → `tests/unit/` — 143 tests, sin base de datos.
- **Taller de Integration Tests** → `tests/integration/` — 21 tests contra la API
  y PostgreSQL reales, más 13 que validan el propio entorno
  (ver [sección 10](#10-pruebas-de-integración)).
- **Taller de Contract Testing (Pact)** → `tests/contract/` — 5 interacciones
  consumer, 1 verificación de provider y 12 tests que validan el entorno
  (ver [sección 11](#11-contract-testing-con-pact)).

**195 tests · 80 % de cobertura.**

---

## 1. Qué se prueba y qué no

| Capa | Pruebas unitarias | Pruebas de integración |
|---|---|---|
| `domain/` | **Sí** — 115 tests, con objetos reales | Indirectamente, a través de la API |
| `application/use_cases/` | **Sí** — 28 tests, repositorios mockeados | Indirectamente, a través de la API |
| `infrastructure/` | No — requiere PostgreSQL | **Sí** — mapeo ORM ↔ dominio y `commit`/`rollback` |
| `presentation/` | No — es la frontera HTTP | **Sí** — routers, `Depends` y manejadores de excepción |

La división es deliberada: **cada capa se prueba con la herramienta que le
corresponde.** Las reglas de negocio se verifican una sola vez, en las unitarias,
donde son rápidas de escribir y de ejecutar; las de integración no las repiten,
sino que comprueban el *cableado* entre capas, que es justo lo que un mock oculta.

Desde el taller de integración, `infrastructure/` y `presentation/` **ya no están
excluidas** de la medición de cobertura en `pyproject.toml`.

---

## 2. Cómo ejecutar

```bash
# Instalar dependencias (incluye el grupo dev: pytest, pytest-asyncio, pytest-cov, httpx)
uv sync

# Toda la suite (unitarias + integración)
uv run pytest -q

# Solo unitarias / solo integración
uv run pytest tests/unit -q
uv run pytest tests/integration -v

# Solo dominio / solo casos de uso
uv run pytest tests/unit/domain -q
uv run pytest tests/unit/application -q

# Un archivo concreto, con detalle
uv run pytest tests/unit/domain/test_plan_nutricional.py -v

# Filtrar por nombre
uv run pytest -k "duplicado" -v
```

> **Las unitarias no necesitan PostgreSQL.** Si `uv run pytest tests/unit` pasa
> con la base de datos apagada, es la prueba de que los dobles aíslan
> correctamente el dominio de la infraestructura.
>
> **Las de integración sí lo necesitan**, pero no rompen la suite si falta: se
> marcan como `skipped`. Con la base apagada, `uv run pytest` reporta
> `156 passed, 21 skipped`.

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
├── unit/
│   ├── domain/                 # espeja src/plan_nutricional/domain/model/
│   │   ├── test_value_objects.py
│   │   ├── test_plan_nutricional.py
│   │   ├── test_plan_dia.py
│   │   ├── test_tiempo_comida.py
│   │   ├── test_receta_catalogo.py
│   │   └── test_plantilla_plan.py
│   └── application/            # espeja src/plan_nutricional/application/use_cases/
│       ├── test_crear_plan.py
│       ├── test_agregar_dia.py
│       ├── test_cambiar_estado_plan.py
│       ├── test_agregar_receta_desde_catalogo.py
│       └── test_crear_plan_desde_plantilla.py
├── integration/                # no espeja src/: se organiza por flujo, no por capa
│   ├── conftest.py             # motor, transacción reversible y cliente HTTP
│   ├── test_planes_api_flujo_correcto.py
│   ├── test_planes_api_flujo_incorrecto.py
│   └── test_convenciones_del_entorno.py   # guardián de las reglas (sección 9)
└── contract/                   # Pact: se organiza por rol (sección 11)
    ├── conftest.py             # carpeta pacts/, contrato_limpio, mock_server
    ├── consumer/
    │   ├── cliente_planes.py                        # cliente de "app-paciente"
    │   ├── test_app_paciente_consume_planes.py      # 3 interacciones
    │   └── test_plan_nutricional_consume_pacientes.py  # 2 interacciones
    ├── provider/
    │   ├── app_provider.py                          # app real + provider states
    │   └── test_verificar_planes_provider.py        # verificación con Pact
    └── test_convenciones_contrato.py                # guardián de las reglas
```

`tests/integration/` **no espeja la estructura de `src/`**, y es a propósito: una
prueba de integración no corresponde a un módulo, sino a un *recorrido* que
atraviesa varios. Por eso se organiza por flujo (correcto / incorrecto).

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
| **Subtotal unitarias** | **143** | |
| `integration/test_planes_api_flujo_incorrecto.py` | 13 | Errores 404 / 409 / 422 y ausencia de escritura tras el fallo |
| `integration/test_convenciones_del_entorno.py` | 13 | Guardián: mocks, borrados, aislamiento, naming, Postman |
| `integration/test_planes_api_flujo_correcto.py` | 8 | Ciclo de vida completo del plan, consultas y aislamiento |
| **Subtotal integración** | **34** | |
| **Total** | **177** | |

---

## 7. Cobertura

Resultado de `uv run pytest --cov --cov-report=term-missing` con PostgreSQL
levantado:

| Módulo | Cobertura |
|---|---|
| `domain/model/plan_nutricional.py` | 100 % |
| `domain/model/value_objects.py` | 100 % |
| `domain/model/receta_catalogo.py` | 100 % |
| `infrastructure/persistence/orm_models.py` | 100 % |
| `presentation/api/schemas/schemas.py` | 100 % |
| `domain/model/tiempo_comida.py` | 98 % |
| `domain/model/plan_dia.py` | 98 % |
| `domain/model/plantilla_plan.py` | 88 % |
| `presentation/api/exception_handlers.py` | 83 % |
| `infrastructure/persistence/plan_repository_impl.py` | 83 % |
| `presentation/api/routers/planes.py` | 76 % |
| `presentation/api/routers/plantillas.py` | 53 % |
| `presentation/api/routers/catalogo_recetas.py` | 52 % |
| **Total** | **79 %** |

El total **baja** de 82 % a 79 % respecto al taller anterior, y eso es una buena
señal, no un retroceso: antes se medían solo dos capas de cuatro. Ahora se mide
todo el microservicio, y los módulos con menor cobertura señalan con exactitud lo
que falta por cubrir — los routers de catálogo y plantillas, que quedaron fuera
del alcance de este avance.

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

En `.claude/` hay **dos parejas** de piezas, una por cada tipo de prueba:

| Pieza | Unitarias | Integración |
|---|---|---|
| **Subagente** — *quién* hace el trabajo | `.claude/agents/test-writer.md` | `.claude/agents/integration-test-writer.md` |
| **Skill** — *cómo* se hace | `.claude/skills/testing-plan-nutricional/` | `.claude/skills/integration-testing-plan-nutricional/` |

Cada agente, en el paso 2 de su flujo, consulta su skill: así el conocimiento vive
en un solo sitio y no se duplica. Las dos skills se remiten entre sí en lugar de
repetir contenido, y **los alcances no se solapan**: el `test-writer` tiene
prohibido tocar `tests/integration/` y `postman/`, y el `integration-test-writer`
tiene prohibido tocar `tests/unit/` y `tests/conftest.py`. Si le pides al
`test-writer` que cubra un router, su instrucción es decirlo y detenerse en vez de
escribir una unitaria con mocks que no probaría el cableado.

```
# Cargar las convenciones en la conversación actual
/testing-plan-nutricional
/integration-testing-plan-nutricional

# Delegar en el subagente que corresponda
"usa el test-writer para cubrir eliminar_dia.py"
"usa el integration-test-writer para cubrir el router de catálogo"
```

### Qué hace que el entorno esté *validado*

No basta con escribir las reglas en un documento: un documento no impide nada.
Este entorno se apoya en tres niveles, de menor a mayor garantía.

**1. El flujo del agente le obliga a demostrar su trabajo.** Ninguno de los dos
puede terminar sin haber ejecutado `uv run pytest` y reportado la salida real y
las líneas sin cubrir. El `integration-test-writer` debe además ejecutar el
guardián del entorno y **comprobar el conteo de filas de la base antes y después**
— la prueba de que sus tests no ensuciaron nada.

**2. Prohibiciones explícitas que cierran los atajos conocidos.** Ninguno puede
modificar `src/` para hacer pasar un test (si un test revela un bug, debe
documentarlo y detenerse), ni añadir `# pragma: no cover`, ni relajar el guardián.
El de integración tampoco puede tocar la fixture `cliente` para "arreglar" un test
suyo: si sospecha del aislamiento, debe pararse y explicarlo.

**3. Un guardián automático que comprueba las reglas.** Es la diferencia entre un
entorno documentado y uno validado:

```
tests/integration/test_convenciones_del_entorno.py    ← 13 tests
```

Verifica por análisis estático de los propios archivos que no hay mocks en
integración, que nadie introdujo un `TRUNCATE`/`DROP`/`CREATE DATABASE`, que el
`conftest` conserva las tres piezas del aislamiento transaccional, que los
archivos llevan su marcador, que los nombres describen el resultado esperado, que
no se depende de la fecha actual, y que la colección de Postman sigue cubriendo
ambos flujos con aserciones.

No lleva el marcador `integration` y no toca la base: sigue protegiendo el
repositorio aunque no haya Docker levantado.

Que el guardián funciona se comprueba rompiéndolo a propósito. Con un archivo que
viola cuatro reglas a la vez, esto es lo que reporta:

```
AssertionError: Las pruebas de integración no admiten dobles de prueba.
                Encontrado: ['...: AsyncMock', '...: unittest.mock']
AssertionError: Ninguna prueba de integración puede borrar ni crear bases o tablas:
                el rollback ya aísla cada test. Encontrado: ['...: TRUNCATE']
AssertionError: Archivos sin `pytestmark`: ['...']
AssertionError: Estos nombres no describen acción, condición y resultado esperado:
                ['test_malo']
```

Un detalle que costó afinar: el guardián analiza **código, no prosa**. La primera
versión marcaba como infracción la frase *"esto sustituye al `plan_repo_mock` de
las unitarias"* escrita en un docstring, y la forma de "arreglarlo" habría sido
empeorar la documentación. Ahora `codigo_efectivo()` elimina docstrings y
comentarios antes de escanear, pero **conserva las cadenas normales**: un
`TRUNCATE` dentro de un `text("...")` es código ejecutable y sí debe detectarse.

## 10. Pruebas de integración

Aplicación del **taller de Integration Tests** al caso de estudio. Alcance de
este avance: el agregado principal, **PlanNutricional**.

### 10.1 Qué cambia respecto a una prueba unitaria

|  | Unitaria | Integración |
|---|---|---|
| Dobles de prueba | `AsyncMock(spec=Puerto)` | **Ninguno** |
| Base de datos | No se usa | PostgreSQL real |
| Punto de entrada | El caso de uso, en Python | Una petición HTTP |
| Qué demuestra | Que la **regla de negocio** es correcta | Que el **cableado** entre capas funciona |

El recorrido completo de cada test es:

```
HTTP → router → caso de uso → repositorio SQLAlchemy → PostgreSQL → HTTP
```

Un mock es útil precisamente porque oculta la infraestructura; el precio es que
oculta también sus fallos. Estas pruebas cubren tres cosas que las unitarias no
pueden ver, por buenas que sean:

1. **El mapeo dominio ↔ ORM.** Que `plan_repository_impl.py` sabe guardar la
   jerarquía plan → día → tiempo de comida → receta y volver a reconstruirla.
2. **La traducción de errores.** Que `exception_handlers.py` convierte cada
   excepción de dominio en el status HTTP y el código `tipo` que promete el
   README (404 / 409 / 422).
3. **El `commit` y el `rollback`.** Que tras un error no queda nada escrito.

### 10.2 Los dos flujos

**Flujo correcto** (`test_planes_api_flujo_correcto.py`). El test principal es
uno solo y largo, deliberadamente: partirlo rompería lo que se quiere demostrar,
que es que el estado sobrevive de una petición a la siguiente.

```
POST   /planes                                             → 201  (guarda plan_id)
POST   /planes/{id}/dias                     {numero_dia: 1}   → 204
POST   /planes/{id}/dias/1/tiempos           {tipo: DESAYUNO}  → 204
POST   /planes/{id}/dias/1/tiempos/DESAYUNO/recetas  {...}     → 204
GET    /planes/{id}                                        → 200  jerarquía completa
PATCH  /planes/{id}/recomendacion                          → 204  + GET lo confirma
PATCH  /planes/{id}/estado          {nuevo_estado: FINALIZADO} → 204  + GET lo confirma
```

**Flujo incorrecto** (`test_planes_api_flujo_incorrecto.py`). Cada test viola una
regla y comprueba el status y el `tipo` devueltos:

| Escenario | Respuesta |
|---|---|
| Obtener un plan inexistente | 404 |
| Agregar un día a un plan inexistente | 404 `PLAN_NO_ENCONTRADO` |
| Agregar un tiempo de comida a un día inexistente | 404 `DIA_NO_ENCONTRADO` |
| Agregar un día duplicado | 409 `DIA_DUPLICADO` |
| Agregar un tiempo de comida duplicado | 409 `TIEMPO_COMIDA_DUPLICADO` |
| Agregar una receta con nombre duplicado en mayúsculas | 409 `RECETA_DUPLICADA` |
| Modificar un plan FINALIZADO | 409 `PLAN_NO_MODIFICABLE` |
| Reactivar un plan FINALIZADO | 409 `TRANSICION_ESTADO_INVALIDA` |
| Agregar el día 16 a un plan de 15 días | 422 `DIA_FUERA_DE_DURACION` |
| Crear un plan de 20 días | 422 `VALOR_INVALIDO` |
| Crear un plan con la recomendación vacía | 422 `VALOR_INVALIDO` |
| Crear un plan sin `paciente_id` | 422 de Pydantic |
| Usar un tiempo de comida `BRUNCH` | 422 de Pydantic |

> **La regla del camino de error, versión integrada.** En las unitarias, cada
> rama de error termina en `plan_repo_mock.guardar.assert_not_awaited()`. Aquí el
> equivalente es un `GET` posterior que comprueba que el plan quedó intacto — y
> eso sí prueba de verdad que el `rollback` funciona, cosa que un mock no puede
> confirmar.

### 10.3 Cómo se montan (`tests/integration/conftest.py`)

Tres decisiones sostienen el módulo:

**1. Una sola base de datos, y no se ensucia.** Se usa `db_plan_nutricional`, la
misma del docker-compose: no se crea ninguna base de prueba aparte. Lo que evita
que los tests dejen basura es que **cada test corre dentro de una transacción que
se revierte al terminar**.

El problema a resolver es que la aplicación hace `commit()` al final de cada
petición. Si ese commit llegara a la base, cada test dejaría filas sueltas. La
solución tiene tres pasos, todos en la fixture `cliente`:

```python
conexion = await motor_test.connect()
transaccion = await conexion.begin()               # 1. transacción externa

fabrica_sesion = async_sessionmaker(
    bind=conexion,
    join_transaction_mode="create_savepoint",      # 2. el commit() de la app
    expire_on_commit=False,                        #    solo libera un SAVEPOINT
)
...
await transaccion.rollback()                       # 3. se deshace todo
```

Con `join_transaction_mode="create_savepoint"`, el `commit()` de cada petición no
confirma nada de verdad: libera un SAVEPOINT dentro de la transacción externa,
que sigue abierta. Al acabar el test, un `rollback()` borra todo de golpe.

Dos consecuencias que importan:

- Las peticiones **sí se ven entre sí** (comparten transacción), que es justo lo
  que necesita un flujo end-to-end para ser realista.
- El `rollback()` de una petición fallida revierte solo hasta su SAVEPOINT, no lo
  anterior — exactamente el comportamiento de producción. Por eso los tests del
  flujo incorrecto pueden comprobar que un error no borró lo que ya estaba.

Como nada se confirma, no hace falta `TRUNCATE` entre tests ni una base aparte, y
la suite es más rápida. Los tests
`test_aislamiento_paso_1_*` y `test_aislamiento_paso_2_*` lo demuestran: el
primero crea un plan para un paciente fijo, el segundo comprueba que ya no
existe.

> **Corolario para escribir tests:** como la base puede tener datos previos,
> ningún test debe asumir que está vacía. Se comprueba **pertenencia**
> (`plan_id in ids`) y no igualdad de listados, y las consultas se acotan a un
> `paciente_id` generado con `uuid4()` en el propio test.

**2. Un solo punto de inyección.** Los tres routers definen cada uno su propio
`_get_repo` — son objetos de función **distintos**, así que sobrescribirlos uno a
uno sería frágil. Pero todos acaban dependiendo de la misma hoja compartida:

```python
app.dependency_overrides[get_db_session] = _sesion_de_test
```

Esa única línea redirige toda la aplicación a la conexión de prueba. La sesión de
test replica el contrato de la de producción (`commit` al salir, `rollback` ante
excepción); sin el `commit`, ni siquiera el SAVEPOINT se liberaría y el flujo
correcto no probaría nada.

**3. No hace falta levantar uvicorn.** `httpx.AsyncClient` con `ASGITransport`
habla con la app en el mismo proceso, pero pasando por routers, `Depends`,
validación de Pydantic y manejadores de excepción. Es tan real como una petición
de red, y mucho más rápido.

### 10.4 Cómo ejecutarlas

```powershell
# 1. Levantar PostgreSQL (el mismo de siempre, no hace falta nada más)
docker compose -f ms-plan-nutricional-docker-compose.yml up -d

# 2. Correr solo las de integración
uv run pytest tests/integration -v

# 3. O toda la suite
uv run pytest
```

Sin Docker no falla nada: la fixture detecta que PostgreSQL no responde y hace
`pytest.skip`, con lo que `uv run pytest` reporta `156 passed, 21 skipped`.
El guardián del entorno sigue corriendo, porque no toca la base.

Para apuntar a otro servidor, `TEST_DATABASE_URL` tiene prioridad sobre
`settings.database_url`.

**Cómo comprobar que no ensucian la base.** Es fácil de verificar a mano:

```powershell
docker exec plan_nutricional_db psql -U postgres -d db_plan_nutricional -t -c "SELECT count(*) FROM planes_nutricionales;"
uv run pytest tests/integration -q
docker exec plan_nutricional_db psql -U postgres -d db_plan_nutricional -t -c "SELECT count(*) FROM planes_nutricionales;"
```

El conteo es idéntico antes y después, por muchas veces que se repita.

### 10.5 Los mismos flujos en Postman

En `postman/` está la colección equivalente, para ejecutar las pruebas contra la
API levantada de verdad:

```bash
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
uv run fastapi dev main.py          # en otra terminal

newman run postman/ms-plan-nutricional.postman_collection.json \
       -e postman/ms-plan-nutricional.postman_environment.json
```

También se importa directamente en Postman (**Import** → los dos archivos) y se
ejecuta con el *Collection Runner*. Tiene las mismas dos carpetas —
`01 — Flujo correcto` y `02 — Flujo incorrecto` — con 34 aserciones `pm.test`.
Las peticiones de la carpeta 01 son dependientes entre sí (la primera guarda
`plan_id` en una variable de colección), así que hay que ejecutarlas **en orden**.

> **Diferencia importante con pytest.** Postman habla con la API por la red, así
> que no puede envolver nada en una transacción: **sus peticiones sí escriben** en
> `db_plan_nutricional`. Es el precio de probar el servicio tal como está
> desplegado. Cada corrida genera un `paciente_id` nuevo con `{{$guid}}`, de modo
> que la colección se puede repetir sin chocar consigo misma; si quieres dejar la
> base como estaba, bórralos después:
>
> ```powershell
> docker exec plan_nutricional_db psql -U postgres -d db_plan_nutricional -c "TRUNCATE planes_nutricionales CASCADE;"
> ```

## 11. Contract testing con Pact

Aplicación del **taller de Contract Testing** al caso de estudio, con
[pact-python](https://github.com/pact-foundation/pact-python) v3.

### 11.1 Conceptos

Una prueba de contrato comprueba que **dos servicios siguen entendiéndose**
(mismas rutas, mismos campos, mismos tipos) sin tener que desplegarlos juntos.

| Concepto | Qué es |
|---|---|
| **Consumer** | Servicio que hace la petición. **Escribe** el contrato. |
| **Provider** | Servicio que responde. **Verifica** el contrato contra su API real. |
| **Interacción** | Una petición y la respuesta que el consumer espera. |
| **Pact file** | El JSON con las interacciones: `pacts/<consumer>-<provider>.json`. |
| **Provider state** | La precondición (`given(...)`) que el provider prepara antes de cada interacción. |
| **Matchers** | Reglas de tipo o forma (`uuid`, `integer`, `regex`, `each_like`…) en vez de valores exactos. |

Flujo: el test consumer genera el pact → el provider lo reproduce contra su API →
si todo cumple, los dos servicios son compatibles.

### 11.2 Relaciones cubiertas

```
app-paciente ────────────▶ ms-plan-nutricional     ✅ verificado en este repo
  GET /planes/{id}            → 200 (plan con días, tiempos y recetas)
  GET /planes/paciente/{id}   → 200 (lista de planes)
  GET /planes/{id}            → 404 (plan inexistente)

ms-plan-nutricional ─────▶ ms-pacientes            ⏳ lo verifica el equipo de ms-pacientes
  GET /pacientes/{id}         → 200 (nombre, código, identificación)
  GET /pacientes/{id}         → 404 (PacienteNoEncontradoError)
```

- **`app-paciente`** es un consumer simulado: la app móvil del paciente (HU-18).
  Su cliente, `ClientePlanes`, vive en `tests/contract/consumer/cliente_planes.py`.
- En la segunda relación, **ms-plan-nutricional es el consumer**. El contrato sale
  del adaptador real `PacienteGatewayHttp`
  (`src/plan_nutricional/infrastructure/gateways/paciente_gateway_http.py`), que
  implementa el puerto `PacienteGateway`. El pact generado se entrega a ms-pacientes.

### 11.3 Cómo se verifica el provider sin ensuciar la base

`tests/contract/provider/app_provider.py` **monta la app real** dentro de una app
de verificación que añade dos cosas:

1. Una **transacción externa** sobre `db_plan_nutricional`, que se revierte al
   apagar uvicorn. Las sesiones de la app usan `create_savepoint`, igual que en §10.
2. La ruta **`POST /_pact/provider-states`**. Pact la llama antes de cada
   interacción (`setup`: abre un SAVEPOINT y crea el plan con el repositorio real)
   y después (`teardown`: revierte ese SAVEPOINT).

Así cada interacción empieza limpia, y al final la base queda igual que antes.

### 11.4 Cómo ejecutar

```powershell
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
uv run pytest tests/contract/consumer -v                       # 1. genera pacts/
uv run pytest tests/contract/provider -v                       # 2. verifica el contrato
uv run pytest tests/contract/test_convenciones_contrato.py -v  # 3. guardián (sin Docker)
uv run pytest -m contract                                      # solo contratos
```

Salida de la verificación:

```
Verifying a pact between app-paciente and ms-plan-nutricional
  una petición para listar los planes de un paciente
     Given existe un plan activo
    returns a response which
      has status code 200 (OK)
      includes headers "Content-Type" with value "application/json" (OK)
      has a matching body (OK)
  una petición para obtener un plan existente ...                      (OK)
  una petición para obtener un plan que no existe  → 404 ...           (OK)
```

**Prueba negativa.** Si el consumer pasa a esperar `estado_plan` en vez de
`estado`, la verificación falla con:

```
$.estado_plan -> Actual map is missing the following keys: estado_plan
```

Esto es justo lo que el contract testing debe detectar: un cambio en un lado que
el otro lado no soporta.

### 11.5 Entorno para IA: `pact-writer`

| Pieza | Ruta |
|---|---|
| Subagente | `.claude/agents/pact-writer.md` |
| Skill | `.claude/skills/contract-testing-plan-nutricional/SKILL.md` |
| Guardián | `tests/contract/test_convenciones_contrato.py` (12 tests) |

El guardián comprueba automáticamente que:

- cada pact tiene al menos 2 interacciones;
- todas las interacciones tienen su provider state;
- las respuestas usan matchers;
- los tests consumer usan el cliente real (sin mocks ni `httpx` directo);
- cada estado tiene handler;
- la app del provider solo aísla por rollback;
- la ruta de estados nunca aparece en `src/`.

El agente, además, tiene que ejecutar la prueba negativa y comparar el conteo de
filas de la base antes y después.

### 11.6 Problemas encontrados

- **Falso `Missing request` en Windows.** El núcleo Rust de Pact puede responder
  antes de registrar la petición. `mock_server(pact)` espera la coincidencia antes
  de cerrar el mock.
- **`match.date` usa formato strftime** (`%Y-%m-%d`). Con `yyyy-MM-dd`, el
  provider falla aunque la fecha sea correcta.
- **Los `Decimal` se serializan como cadena** (`"2000.00"`), por eso se validan
  con `match.regex`.
