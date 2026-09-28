# Guion del video — Capa de testing de `ms-plan-nutricional`

Duración objetivo: **6 a 8 minutos**. Presentación individual, clara y concisa.

---

## 0. Antes de grabar (checklist, no sale en el video)

- [x] Todos los tests en verde (265 unitarios · 317 en la suite completa).
- [x] Reporte de cobertura regenerado: **81.88 %** en unitarias, **89 %** con la suite completa.
- [ ] Docker Desktop abierto.
- [ ] Terminal con fuente grande (zoom ≥ 130 %), en la raíz del repo.
- [ ] VS Code abierto con el árbol de carpetas visible.
- [ ] Ensayo previo de todos los comandos (la primera ejecución de `uv` puede tardar).
- [ ] Cerrar notificaciones y pestañas con datos personales.

Preparación en terminal:

```powershell
uv sync
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
```

---

## 1. Introducción (≈ 30 s)

**Pantalla:** README del repo.

**Qué decir:**
> "Soy Luis Humberto Navarro. Presento la capa de testing del microservicio
> `ms-plan-nutricional`, el BC3 de Planificación Nutricional de NUR-TRICENTER.
> Es una API en FastAPI con SQLAlchemy async y PostgreSQL, organizada con Clean
> Architecture y DDD. Voy a mostrar las pruebas unitarias con su reporte de cobertura,
> las pruebas de integración agrupadas por flujo y las skills que usé para generarlas."

---

## 2. Estructura de las pruebas (≈ 45 s)

**Pantalla:** árbol de `tests/` en VS Code.

```
tests/
├── conftest.py          ← fixtures compartidas (construir_plan, repos mock…)
├── unit/                ← sin base de datos
│   ├── domain/          ← agregados, entidades, value objects
│   ├── application/     ← un archivo por caso de uso
│   ├── presentation/    ← mappers, excepción→HTTP, composición de la app
│   └── infrastructure/  ← gateway mock de pacientes
├── integration/         ← API real + PostgreSQL real
│   ├── test_planes_api_flujo_correcto.py
│   ├── test_planes_api_flujo_incorrecto.py
│   └── test_convenciones_del_entorno.py   ← guardián
└── contract/            ← Pact (consumer / provider)
```

**Qué decir:**
> "Separo las pruebas por I/O: las unitarias no tocan la base, las de integración
> usan la API y PostgreSQL reales, y además hay contract testing con Pact."

---

## 3. Pruebas unitarias (≈ 1 min 15 s)

**Pantalla:** abre `tests/unit/application/test_agregar_dia.py` (o `test_crear_plan.py`).

**Qué señalar en el código:**
- Patrón **AAA** con comentarios `# Arrange / # Act / # Assert`.
- Nombres en español: `test_<accion>_<condicion>_<resultado>`.
- Repositorios doblados con `AsyncMock(spec=PuertoABC)`, porque sin `spec` un método mal escrito pasaría en verde.
- `assert_awaited_once_with` en el camino feliz y `guardar.assert_not_awaited()` en las ramas de error.

Muestra también `tests/unit/domain/test_plan_nutricional.py`, donde se prueban invariantes
(duración 15/30 días, transiciones de estado, plan no modificable).

**Ejecuta:**

```powershell
uv run pytest tests/unit -q
```

**Qué decir:**
> "Son 265 pruebas y corren en segundos sin base de datos."

---

## 4. Reporte de cobertura (≈ 1 min)

**Ejecuta:**

```powershell
uv run pytest tests/unit --cov --cov-report=term-missing `
    --cov-report=html:htmlcov-unit --cov-report=xml:coverage-unit.xml
```

**Pantalla:** al final de la salida, el `TOTAL` y la línea
`Required test coverage of 80.0% reached`.

Luego abre el HTML:

```powershell
start htmlcov-unit/index.html
```

**Qué señalar:**
- El porcentaje total (≥ 80 %).
- Un archivo con cobertura alta, por ejemplo `plan_nutricional.py`.
- En `pyproject.toml`, `fail_under = 80`: si la cobertura baja del umbral, la suite falla.

**Qué decir:**
> "La cobertura oficial se mide solo con la capa unitaria y sin base de datos, y
> da un 82 %, por encima del 80 % exigido. El reporte está versionado en `htmlcov-unit/` y en `coverage-unit.xml`."

---

## 5. Pruebas de integración: los flujos (≈ 2 min)

**Pantalla:** `tests/integration/conftest.py`, solo 15 segundos.

**Qué decir:**
> "Las pruebas usan un cliente httpx sobre la app FastAPI real y una base PostgreSQL real.
> No hay ningún mock. Cada test corre dentro de una transacción que se revierte al final,
> así que la base queda intacta."

### Flujo 1 — Ciclo de vida completo de un plan (camino feliz)

**Pantalla:** `test_planes_api_flujo_correcto.py` → `test_ciclo_de_vida_completo_de_un_plan_persiste_en_la_base`.

Explica los pasos: crear plan → agregar día → agregar tiempo de comida → agregar receta
→ cambiar estado → verificar que todo quedó persistido. Menciona también la consulta de
planes por paciente y el listado de planes activos.

### Flujo 2 — Reglas de negocio y errores (caminos de error)

**Pantalla:** `test_planes_api_flujo_incorrecto.py`.

Señala cómo cada error de dominio se traduce a HTTP:
- **404**: plan o día inexistente.
- **409**: día, tiempo de comida o receta duplicados; plan finalizado que no admite cambios.
- **422**: día fuera de la duración; duración distinta de 15 o 30 días.

**Ejecuta:**

```powershell
uv run pytest tests/integration -v
```

**Qué decir:**
> "Las pruebas se agrupan por flujo, un archivo por flujo. Además, el guardián
> `test_convenciones_del_entorno.py` verifica por análisis estático que ninguna prueba use
> mocks ni borre datos."

### (Opcional, 30 s) Postman

```powershell
uv run fastapi dev main.py
```

Importa `postman/ms-plan-nutricional.postman_collection.json` y su environment, y ejecuta
la colección con el Runner.

---

## 6. Contract testing con Pact (≈ 45 s, opcional pero suma)

**Ejecuta:**

```powershell
uv run pytest tests/contract/consumer -v    # genera los pacts en pacts/
uv run pytest tests/contract/provider -v    # verifica la API real contra el pact
```

**Pantalla:** `pacts/app-paciente-ms-plan-nutricional.json`.

**Qué decir:**
> "Como tercera capa, el consumidor define el contrato y el proveedor lo verifica contra
> la API real con PostgreSQL."

---

## 7. Skills y reglas usadas para generar los tests (≈ 1 min)

**Pantalla:** la carpeta `.claude/`.

```
CLAUDE.md                                        ← reglas del proyecto
.claude/skills/testing-plan-nutricional/         ← convenciones de unit tests
.claude/skills/integration-testing-plan-nutricional/
.claude/skills/contract-testing-plan-nutricional/
.claude/agents/test-writer.md                    ← subagente de unitarias
.claude/agents/integration-test-writer.md        ← subagente de integración
.claude/agents/pact-writer.md                    ← subagente de contratos
```

Abre `SKILL.md` de `testing-plan-nutricional` y muestra una sección (AAA, uso de `AsyncMock(spec=...)`).

**Qué decir:**
> "Generé los tests con Claude Code. Las skills fijan las convenciones y el `CLAUDE.md`
> las reglas del proyecto, por ejemplo no modificar `src/` para que un test pase.
> Cada subagente tiene su propio alcance, sin solaparse con los demás.
> Todo está en el repositorio, como pide la tarea."

---

## 8. Cierre (≈ 20 s)

**Pantalla:** README, sección "Pruebas y Cobertura".

**Qué decir:**
> "En resumen: 265 pruebas unitarias con un 82 % de cobertura, pruebas de
> integración agrupadas en dos flujos sobre la API y la base reales, contratos con Pact
> y las skills que usé para generarlo todo. Todo se ejecuta con `uv run pytest`. Gracias."

---

## Resumen de comandos (en orden)

```powershell
uv sync
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
uv run pytest tests/unit -q
uv run pytest tests/unit --cov --cov-report=term-missing --cov-report=html:htmlcov-unit --cov-report=xml:coverage-unit.xml
start htmlcov-unit/index.html
uv run pytest tests/integration -v
uv run pytest tests/contract/consumer -v
uv run pytest tests/contract/provider -v
```

## Consejos de grabación

- Herramienta: OBS Studio o la grabadora de Windows (`Win + Alt + R`) o Clipchamp.
- Resolución de 1080p y micrófono cerca. Graba cada sección por separado y únelas al final.
- Si un comando tarda, corta la espera en la edición.
- No leas el guion palabra por palabra; úsalo como referencia.
