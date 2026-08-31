---
name: testing-plan-nutricional
description: Convenciones de testing de ms-plan-nutricional — patrón AAA, naming en español, cómo doblar los puertos de repositorio con AsyncMock, y cómo medir cobertura con uv. Úsala al escribir, revisar o depurar cualquier test del proyecto.
---

# Convenciones de testing — ms-plan-nutricional

## 1. Dónde va cada test

| Qué se prueba | Dónde vive el test | Qué doble se usa |
|---|---|---|
| Value Object, entidad, Aggregate Root | `tests/unit/domain/` | ninguno — objetos reales |
| Caso de uso (`use_cases/*.py`) | `tests/unit/application/` | `AsyncMock(spec=<PuertoABC>)` |
| Repositorios, routers, ORM | *fuera de alcance* | — (excluidos de cobertura) |

Fixtures compartidas: `tests/conftest.py`.

## 2. Patrón AAA y naming

Nombre: `test_<accion>_<condicion>_<resultado_esperado>`, en español.

```python
def test_agregar_dia_fuera_de_duracion_lanza_error(construir_plan):
    # Arrange
    plan = construir_plan(dias_duracion=15)

    # Act / Assert
    with pytest.raises(DiaFueraDeDuracionError):
        plan.agregar_dia(16)
```

Cuando Act y Assert son la misma línea (`pytest.raises`), se fusionan los
comentarios en `# Act / Assert`.

## 3. Qué es un mock y por qué se usa aquí

Los casos de uso reciben un repositorio por inyección de dependencias. El
repositorio real habla con PostgreSQL: usarlo en una prueba unitaria obligaría a
levantar la base de datos y haría el test lento y frágil.

Un **mock** es un objeto falso que ocupa el lugar de esa dependencia. Permite dos
cosas:

```python
# (a) Controlar qué devuelve la dependencia
plan_repo_mock.obtener_por_id.return_value = plan

# (b) Verificar cómo se la usó
plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
plan_repo_mock.guardar.assert_awaited_once_with(plan)
```

`AsyncMock` es la variante para dependencias asíncronas (sus métodos se pueden
`await`). Los tres puertos del proyecto son 100 % `async`.

**`spec=` es obligatorio.** `AsyncMock(spec=PlanNutricionalRepository)` obliga al
mock a exponer exactamente los métodos del puerto. Sin `spec`, escribir
`repo.obtner_por_id(...)` devolvería otro mock y el test pasaría en verde
ocultando el error.

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
| Inspeccionar el argumento guardado | `mock.guardar.await_args.args[0]` |

> Nota: para `AsyncMock` se usan las variantes `*_awaited_*`
> (`assert_awaited_once_with`), no `assert_called_once_with`.

## 4. Patrón de test de un caso de uso

Todos los casos de uso siguen la misma forma: `obtener_por_id` → si `None`
lanzar → método de dominio → `guardar`. Por tanto, todos se prueban igual:

```python
async def test_agregar_dia_valido_devuelve_el_dia_y_persiste_el_plan(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias_duracion=15)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarDiaUseCase(plan_repo_mock)

    # Act
    dia = await caso_de_uso.ejecutar(AgregarDiaCommand(plan_id=plan.id, numero_dia=3))

    # Assert
    assert dia.numero_dia == 3
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)
```

Y **cada rama de error** debe comprobar que no se persistió nada:

```python
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(cmd)

    plan_repo_mock.guardar.assert_not_awaited()
```

Con varios repositorios inyectados se puede además verificar el **corto-circuito**:
si el plan no existe, el catálogo ni siquiera debería consultarse
(`catalogo_repo_mock.obtener_por_id.assert_not_awaited()`).

Ejemplos completos ya escritos:
- `tests/unit/application/test_agregar_dia.py` — patrón de referencia.
- `tests/unit/application/test_agregar_receta_desde_catalogo.py` — dos mocks, tres ramas de error, valores por defecto.
- `tests/unit/application/test_crear_plan_desde_plantilla.py` — tres mocks, `side_effect`, `assert_has_awaits`.

## 5. Invariantes del dominio que conviene recordar

- `DuracionPlan` solo admite **15 o 30** días.
- `PlanNutricional.agregar_dia` exige `1 <= numero_dia <= duracion.dias`.
- Transiciones: `ACTIVO → {FINALIZADO, CANCELADO}`; FINALIZADO y CANCELADO son
  terminales. Cualquier otra lanza `TransicionEstadoInvalidaError`.
- Un plan no ACTIVO lanza `PlanNoModificableError` ante cualquier modificación.
- `plan.dias`, `dia.tiempos_comida` y `tiempo.recetas` devuelven **copias
  defensivas**: mutar lo devuelto no altera el agregado (y eso es un test válido).
- `TiempoComida.agregar_receta` compara nombres en minúsculas → duplicado
  case-insensitive.
- `PlantillaPlan` **no** tiene ciclo de vida: siempre es editable.

## 6. Comandos

```powershell
# Suite completa
uv run pytest -q

# Un archivo, con detalle
uv run pytest tests/unit/domain/test_plan_nutricional.py -v

# Filtrar por nombre
uv run pytest -k "duplicado" -v

# Cobertura: terminal + reporte HTML
uv run pytest --cov --cov-report=term-missing --cov-report=html
Start-Process .\htmlcov\index.html
```

Cobertura configurada en `pyproject.toml`: mide el paquete `plan_nutricional` y
excluye `infrastructure/` y `presentation/` (fuera de alcance). No hay umbral
`fail_under`: la cobertura se mide y se reporta, no bloquea la suite.

## 7. Errores frecuentes

- **`AsyncMock()` sin `spec`** → los typos pasan silenciosos. Siempre `spec=`.
- **Cobertura en 0 %** → falta la instalación editable: ejecuta `uv sync`.
- **`assert_called_once_with` en un `AsyncMock`** → usa `assert_awaited_once_with`.
- **Olvidar el orden de los parámetros** de `CrearPlanDesdePlantillaUseCase`:
  es `(plan_repo, plantilla_repo, catalogo_repo)`.
- **Tests dependientes de la fecha actual** → usa fechas fijas.
- **Cambiar el estado del plan antes de agregarle días** en un builder: un plan
  no ACTIVO ya no admite cambios (por eso `construir_plan` cambia el estado al
  final).
