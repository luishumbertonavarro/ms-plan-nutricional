---
name: ci-quality-plan-nutricional
description: Configuración y diagnóstico de la cadena de calidad de ms-plan-nutricional — hook pre-commit con Husky + lint-staged + Ruff, CI en GitHub Actions y escaneo de SonarCloud. Úsala al tocar package.json, .husky/, .github/workflows/, sonar-project.properties o reglas de ruff, o cuando falle un commit, el pipeline o el Quality Gate.
---

# Calidad y CI — ms-plan-nutricional

## 1. Piezas y quién hace qué

| Pieza | Archivo | Qué hace |
|---|---|---|
| Linter | `pyproject.toml` → `[tool.ruff]` | Ruff con `select` explícito: `E4, E7, E9, F, W191, E101` |
| Hook | `.husky/pre-commit` | Ejecuta `npx lint-staged` en cada `git commit` |
| Archivos en staging | `package.json` → `"lint-staged"` | `*.py` → `uv run ruff check --fix` |
| CI | `.github/workflows/ci.yml` | `uv sync --locked` → `ruff check` → `pytest tests/unit --cov` → SonarCloud |
| Análisis estático | `sonar-project.properties` | Organización y projectKey de SonarCloud, `src/` y `tests/`, cobertura desde `coverage.xml` |

El linter es **el mismo** en el hook y en el CI. Si el hook pasa, el paso de lint del CI también pasa. Si cambias las reglas en `pyproject.toml`, ambos lugares quedan actualizados.

## 2. Instalación después de clonar

```bash
uv sync          # Python: dependencias + ruff
npm install      # Node: husky + lint-staged; `prepare` fija core.hooksPath=.husky/_
git config core.hooksPath   # debe imprimir .husky/_
```

## 3. Reglas al modificar

- **No** agregues `ruff format` al hook ni al CI sin decidirlo antes: reescribiría unos 79 archivos. Si se adopta, hazlo en un commit `style:` aislado.
- **No** corras `pre-commit install`. `.pre-commit-config.yaml` es el registro de la tarea anterior y pelearía con Husky por el hook.
- **No** bajes `fail_under` ni ignores reglas de ruff para que el CI pase. Corrige el código o documenta la excepción con `# noqa: <regla>` y una justificación.
- Las versiones de las acciones van fijadas a una versión mayor (`@v4`, `@v6`, `@v5`). No uses `@master`.
- Las pruebas de integración y de contrato **no** corren en el CI básico porque necesitan PostgreSQL. Si se agregan, usa `services: postgres` en el puerto 5434 y `migraciones/001_mensajeria.sql`.

## 4. Diagnóstico

| Síntoma | Causa | Solución |
|---|---|---|
| El commit pasa sin ejecutar el hook | No se corrió `npm install`, o `core.hooksPath` está vacío | `npm install` (o `npx husky`) |
| `uv: command not found` en el hook | Git Bash no ve `uv` | Agregar `~/.local/bin` al PATH de Git Bash |
| `husky - pre-commit script failed` | Ruff encontró un error que no corrige solo | Leer el código de la regla (p. ej. `F821`) y corregir |
| El CI falla en `uv sync --locked` | `uv.lock` está desactualizado | `uv lock` local y commitear el lock |
| El CI falla en pytest con cobertura menor a 80 % | Se agregó código sin pruebas | Escribir pruebas con la skill `testing-plan-nutricional` |
| El paso de Sonar dice "You are running CI analysis while Automatic Analysis is enabled" | Automatic Analysis está activo en SonarCloud | Ir a *Administration → Analysis Method* y desactivarlo |
| El paso de Sonar falla con 401 o "Project not found" | Falta `SONAR_TOKEN`, o la organización o el projectKey no coinciden | Revisar el secret y `sonar-project.properties` |
| Sonar muestra 0 % de cobertura | No encuentra `coverage.xml` | El paso de pytest debe generar `--cov-report=xml:coverage.xml` antes del scan |

## 5. Verificar que el hook bloquea

```bash
printf 'def f():\n    return x_indefinida\n' > src/plan_nutricional/_tmp.py
git add src/plan_nutricional/_tmp.py && git commit -m "prueba"   # debe abortar con F821
git reset -q src/plan_nutricional/_tmp.py && rm src/plan_nutricional/_tmp.py
```
