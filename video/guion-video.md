# Guion del video — Capa de testing de `ms-plan-nutricional`

Duración objetivo: **3 a 4 minutos**. Lee solo lo que está en los bloques de cita (>).

---

## 0. Antes de grabar (no sale en el video)

- [ ] Docker Desktop abierto y la BD levantada (si no, las 22 pruebas de integración salen como *skipped*).
- [ ] Terminal en la raíz del repo, fuente grande.
- [ ] VS Code con el árbol de `tests/` visible.
- [ ] Ensayar los comandos una vez.

```powershell
uv sync
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
```

---

## 1. Intro (≈ 20 s) — pantalla: árbol de `tests/`

> "Soy Luis Humberto Navarro. Presento la capa de testing del microservicio
> ms-plan-nutricional, hecho en FastAPI con PostgreSQL. Tiene tres carpetas:
> unit, que prueba la lógica sin base de datos; integration, que llama a los endpoints
> del propio microservicio contra un PostgreSQL en Docker; y contract, con Pact."

---

## 2. Unitarias + cobertura (≈ 1 min)

**Pantalla:** abre `tests/unit/application/test_agregar_dia.py` unos segundos.

> "Las unitarias siguen el patrón Arrange-Act-Assert y reemplazan la base de datos
> por repositorios falsos hechos con AsyncMock."

**Ejecuta:**

```powershell
uv run pytest tests/unit --cov --cov-report=term-missing --cov-report=html:htmlcov-unit --cov-report=xml:coverage-unit.xml
```

**Pantalla:** la línea final `Required test coverage of 80.0% reached. Total coverage: 83.88%`.

> "Son 265 pruebas y la cobertura es de casi 84 por ciento, por encima del 80 exigido.
> Si baja del 80, la ejecución falla."

```powershell
start htmlcov-unit/index.html
```

> "Este es el reporte HTML, que está versionado en el repositorio."

---

## 3. Integración: dos flujos (≈ 1 min)

**Pantalla:** `tests/integration/test_planes_api_flujo_correcto.py`.

> "Las pruebas de integración se agrupan en dos flujos, un archivo por flujo.
> El flujo correcto recorre el ciclo de vida de un plan: crearlo, agregar día,
> tiempo de comida y receta, y cambiar su estado. Después lo vuelve a leer con un GET
> para comprobar que todo se guardó en la base de datos."

**Pantalla:** `tests/integration/test_planes_api_flujo_incorrecto.py`.

> "El flujo incorrecto prueba las reglas de negocio: 404 si no existe,
> 409 por duplicados o plan finalizado, y 422 por datos inválidos."

**Ejecuta:**

```powershell
uv run pytest tests/integration -v
```

> "No usan mocks, y cada prueba corre en una transacción que se revierte, así la base queda limpia."

---

## 4. Pact (≈ 20 s, opcional)

```powershell
uv run pytest tests/contract -v
```

> "Además hay contract testing con Pact: el consumidor genera el contrato y el proveedor lo verifica."

---

## 5. Skills (≈ 30 s) — pantalla: carpeta `.claude/` y `CLAUDE.md`

> "Los tests los generé con Claude Code. Las skills y los agentes que usé están
> en la carpeta .claude, y las reglas del proyecto en CLAUDE.md."

---

## 6. Cierre (≈ 10 s)

> "En resumen: 265 pruebas unitarias con 84 por ciento de cobertura, dos flujos de integración
> y contratos con Pact. Todo se ejecuta con uv run pytest. Gracias."

---

## Comandos en orden

```powershell
uv sync
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
uv run pytest tests/unit --cov --cov-report=term-missing --cov-report=html:htmlcov-unit --cov-report=xml:coverage-unit.xml
start htmlcov-unit/index.html
uv run pytest tests/integration -v
uv run pytest tests/contract -v
```
