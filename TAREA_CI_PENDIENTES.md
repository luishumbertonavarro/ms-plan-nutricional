# Tarea: Husky + lint-staged + CI (GitHub Actions) + SonarCloud

Estado al **18/11/2026**. Implementado con asistencia de IA (Claude Code).

**Enlace de entrega:** https://github.com/luishumbertonavarro/ms-plan-nutricional

---

## ✅ Lo que se hizo

| Requisito de la tarea | Implementación | Estado |
|---|---|---|
| Configurar Husky y lint-staged | `package.json` (husky ^9, lint-staged ^15, script `prepare`), `.husky/pre-commit` → `npx lint-staged` | ✅ Hecho |
| Forzar el linter antes del commit | lint-staged ejecuta `uv run ruff check --fix` sobre los `*.py` en staging. Si queda un error, el commit se aborta | ✅ Probado localmente: con un `F821` el commit se bloqueó |
| CI en GitHub Actions al hacer push | `.github/workflows/ci.yml`: `uv sync --locked`, luego `ruff check`, luego `pytest tests/unit --cov` (umbral de 80 %), luego SonarCloud | ✅ Primer run: checkout, dependencias, lint y pruebas en verde |
| Escaneo básico de SonarCloud | `sonar-project.properties` + paso `SonarSource/sonarqube-scan-action@v5` | ⚠️ El paso existe; falta confirmar que pase (ver pendientes) |
| Subir skills / CLAUDE.md | `CLAUDE.md` (sección *CI y calidad*) + `.claude/skills/ci-quality-plan-nutricional/SKILL.md` + README (sección de calidad y badges) | ✅ Hecho |

Commits de esta sesión:
- `chore: husky + lint-staged con ruff en pre-commit`
- `ci: GitHub Actions (uv, ruff, pytest + cobertura) y SonarCloud`
- `docs: CLAUDE.md, skill ci-quality-plan-nutricional y README de calidad/CI`
- `docs: aviso de lo hecho y lo pendiente de la tarea de CI` (este archivo)

Resultados locales: `ruff check` sin errores, 82,05 % de cobertura en las pruebas unitarias.

---

## ⏳ Lo que falta (pasos manuales)

1. **SonarCloud**: confirmar que esté configurado.
   - [ ] Entrar a https://sonarcloud.io con GitHub e importar el repo `ms-plan-nutricional`.
   - [ ] Verificar que la **organización** sea `luishumbertonavarro` y el **project key** sea `luishumbertonavarro_ms-plan-nutricional`. Si SonarCloud asigna otros, cambiarlos en `sonar-project.properties`.
   - [ ] En *Administration → Analysis Method*, **desactivar Automatic Analysis**. Si queda activo, el scan del CI falla.
   - [ ] Generar un token en SonarCloud (*My Account → Security*).
   - [ ] En GitHub, ir a *Settings → Secrets and variables → Actions → New repository secret* y crear `SONAR_TOKEN`.
2. **Verificar el CI**
   - [ ] En la pestaña **Actions**, el último run de *CI* debe estar en verde, incluido el paso *SonarCloud Scan*. Si falló solo Sonar, configurar el punto 1 y usar **Re-run jobs**.
   - [ ] En SonarCloud debe aparecer el análisis con la cobertura importada (alrededor de 82 %).
   - [ ] Los badges del README (CI y Quality Gate) deben mostrarse correctamente.
3. **Evidencia para la entrega** (opcional pero recomendable)
   - [ ] Captura de un commit bloqueado por el hook. Los pasos para reproducirlo están en la skill, §5.
   - [ ] Captura del run en verde en Actions.
   - [ ] Captura del dashboard de SonarCloud.

---

## 📝 Notas

- **Activar el hook después de clonar:** `uv sync && npm install`. El script `prepare` fija `core.hooksPath=.husky/_`.
- **No se agregó `ruff format`**, por la decisión de la tarea anterior (reescribiría unos 79 archivos). Si se pide formateo, hay que agregar `"uv run ruff format"` en `lint-staged` dentro de `package.json` y hacer un commit `style:` que formatee todo el repo.
- **`.pre-commit-config.yaml` (tarea anterior) ya no se ejecuta** porque ahora manda Husky. Se conserva como registro. No correr `pre-commit install`.
- **El CI básico solo corre las pruebas unitarias.** Las de integración y contrato necesitan PostgreSQL.
- Diagnóstico de fallos del hook, del CI o de Sonar: ver `.claude/skills/ci-quality-plan-nutricional/SKILL.md`.
