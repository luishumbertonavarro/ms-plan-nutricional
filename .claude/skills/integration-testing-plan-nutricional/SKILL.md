---
name: integration-testing-plan-nutricional
description: Convenciones de pruebas de integración de ms-plan-nutricional — cliente httpx sobre la app FastAPI real, aislamiento por transacción reversible sobre PostgreSQL, mapeo de errores de dominio a HTTP y sincronización con la colección Postman. Úsala al escribir, revisar o depurar cualquier test de tests/integration/ o la colección de postman/.
---

# Convenciones de pruebas de integración — ms-plan-nutricional

Complemento de la skill `testing-plan-nutricional`, que cubre las **unitarias**.
Aquí solo se trata `tests/integration/` y `postman/`.

## 1. Qué es una prueba de integración en este proyecto

Recorre el camino completo, **sin ningún doble de prueba**:

```
HTTP → router → caso de uso → repositorio SQLAlchemy → PostgreSQL → HTTP
```

|  | Unitaria (`tests/unit/`) | Integración (`tests/integration/`) |
|---|---|---|
| Dobles | `AsyncMock(spec=Puerto)` | **ninguno** |
| Base de datos | no se usa | PostgreSQL real |
| Entrada | el caso de uso, en Python | una petición HTTP |
| Qué demuestra | la **regla de negocio** es correcta | el **cableado** entre capas funciona |

**Regla para decidir dónde va un test:** si prueba una regla de negocio, va en
`tests/unit/` con mocks. Si prueba el cableado —que el ORM persiste bien, que un
error de dominio sale como 409, que el `rollback` funciona—, va aquí.

**Nunca repitas aquí una regla de negocio ya cubierta en unitarias.** Sería más
lenta y no aportaría nada. Estas pruebas existen para ver lo que un mock oculta:

1. El **mapeo dominio ↔ ORM** (`plan_repository_impl.py` guarda y reconstruye la
   jerarquía plan → día → tiempo de comida → receta).
2. La **traducción de errores** (`exception_handlers.py` → status HTTP + código
   `tipo`).
3. El **`commit` y el `rollback`** de `get_db_session`.

## 2. El aislamiento — lo más importante de este módulo

**Se usa `db_plan_nutricional`, la misma base de desarrollo, y no se ensucia.**
No hay base de prueba aparte, no hay `TRUNCATE`, no hay `CREATE DATABASE`.

El problema: la app hace `commit()` al final de cada petición. Si ese commit
llegara a la base, cada test dejaría filas sueltas. La solución, en la fixture
`cliente` de `tests/integration/conftest.py`:

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

Consecuencias que hay que tener presentes al escribir tests:

- Las peticiones **sí se ven entre sí** (comparten transacción). Por eso un flujo
  end-to-end de varias peticiones es realista.
- El `rollback()` de una petición fallida revierte solo hasta su SAVEPOINT, no lo
  anterior — igual que en producción. Por eso el flujo incorrecto puede comprobar
  que un error no borró lo que ya estaba guardado.
- **Ningún test puede asumir que la base está vacía.** Comprueba pertenencia
  (`plan_id in ids`), nunca igualdad de listados completos, y acota las consultas
  a un `paciente_id` generado con `uuid4()` dentro del propio test.

> **Prohibido:** añadir `TRUNCATE`, `DELETE`, `DROP` o cualquier escritura fuera
> de esa transacción; crear una base de datos aparte; o commitear con un motor
> distinto del de la fixture. Rompe la garantía de que la suite no ensucia nada.

## 3. Patrón de un test

Mismo AAA y mismo naming en español que las unitarias. Los archivos llevan
`pytestmark = pytest.mark.integration` y los tests reciben la fixture `cliente`
(un `httpx.AsyncClient` sobre la app FastAPI real vía `ASGITransport`).

```python
async def test_agregar_dia_duplicado_devuelve_409_y_no_lo_persiste(cliente):
    # Arrange
    plan_id = (await cliente.post("/planes", json=cuerpo_plan(str(uuid4())))).json()["id"]
    await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Act
    respuesta = await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Assert
    assert respuesta.status_code == 409
    assert respuesta.json()["tipo"] == "DIA_DUPLICADO"

    # El equivalente integrado de `guardar.assert_not_awaited()`
    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert len(plan["dias"]) == 1
```

Dos reglas propias de esta carpeta:

1. **Verifica siempre el código `tipo`, no solo el status.** Es el contrato que
   documenta el README y lo que produce `exception_handlers.py`. Un test que solo
   mira el 409 no distingue `DIA_DUPLICADO` de `PLAN_NO_MODIFICABLE`.
2. **Todo camino de error termina releyendo el recurso** para comprobar que no se
   escribió nada. Es lo que en unitarias hace
   `plan_repo_mock.guardar.assert_not_awaited()`, pero aquí prueba de verdad que
   el `rollback` funciona.

Los endpoints de mutación devuelven **204 sin cuerpo**, así que el estado
resultante siempre se verifica con un `GET` posterior. Eso es una ventaja: obliga
a comprobar lo que quedó en la base, no lo que devolvió el handler.

## 4. Dónde va cada cosa

| Archivo | Contenido |
|---|---|
| `tests/integration/conftest.py` | `url_bd`, `comprobar_bd`, `motor_test`, `cliente` |
| `tests/integration/test_planes_api_flujo_correcto.py` | camino feliz + helper `cuerpo_plan()` |
| `tests/integration/test_planes_api_flujo_incorrecto.py` | 404 / 409 / 422 + helper `_crear_plan()` |
| `tests/integration/test_convenciones_del_entorno.py` | guardián automático de estas reglas |

Las fixtures de `tests/conftest.py` (builders de dominio y `AsyncMock`) **no se
usan aquí**: son mundos separados. Si `cuerpo_plan()` te sirve, impórtalo desde
`tests.integration.test_planes_api_flujo_correcto`.

## 5. Mapa de errores del dominio a HTTP

Lo produce `presentation/api/exception_handlers.py`. Al escribir un test de
camino incorrecto, este es el contrato a verificar:

| Situación | Status | `tipo` |
|---|---|---|
| `*NoEncontrado*` / `*NoEncontrada*` | 404 | `PLAN_NO_ENCONTRADO`, `DIA_NO_ENCONTRADO`, … |
| `PlanNoModificableError` | 409 | `PLAN_NO_MODIFICABLE` |
| `TransicionEstadoInvalidaError` | 409 | `TRANSICION_ESTADO_INVALIDA` |
| `*Duplicado*` / `*Duplicada*` | 409 | `DIA_DUPLICADO`, `TIEMPO_COMIDA_DUPLICADO`, `RECETA_DUPLICADA` |
| `RecetaCatalogoInactivaError` | 409 | `RECETA_CATALOGO_INACTIVA` |
| `*FueraDeDuracion*` | 422 | `DIA_FUERA_DE_DURACION` |
| Cualquier otro `ValueError` de dominio | 422 | `VALOR_INVALIDO` |
| Cuerpo o parámetro inválido | 422 | *(sin `tipo`: es la lista de errores de Pydantic)* |

Ojo con el último: los 422 de Pydantic traen `detail` como **lista** de errores
por campo, no como string. Se comprueban así:

```python
campos = [error["loc"][-1] for error in respuesta.json()["detail"]]
assert "paciente_id" in campos
```

## 6. Comandos

```powershell
# Levantar la base (una vez)
docker compose -f ms-plan-nutricional-docker-compose.yml up -d

# Solo integración
uv run pytest tests/integration -v

# Por marcador, desde cualquier ruta
uv run pytest -m integration

# Toda la suite
uv run pytest
```

Sin PostgreSQL levantado, `comprobar_bd` hace `pytest.skip` y la suite reporta
`156 passed, 21 skipped`. **Nunca hagas que una prueba de integración rompa la
suite de quien no tiene Docker arriba.**

### El guardián del entorno

`tests/integration/test_convenciones_del_entorno.py` comprueba automáticamente
las reglas de esta skill: que no haya mocks, que nadie borre datos, que el
`conftest` conserve el aislamiento transaccional, que los nombres sean
descriptivos y que la colección de Postman siga cubriendo ambos flujos.

```powershell
uv run pytest tests/integration/test_convenciones_del_entorno.py -v
```

No lleva el marcador `integration` y no toca la base: es análisis estático, así
que protege el repositorio incluso sin Docker. **Nunca lo relajes para que pase
un test tuyo**: si te estorba, es que estás rompiendo una regla.

### Verificar que la suite no ensucia la base

Es la comprobación que valida todo el montaje. Debe dar el mismo número antes y
después:

```powershell
docker exec plan_nutricional_db psql -U postgres -d db_plan_nutricional -t -c "SELECT count(*) FROM planes_nutricionales;"
uv run pytest tests/integration -q
docker exec plan_nutricional_db psql -U postgres -d db_plan_nutricional -t -c "SELECT count(*) FROM planes_nutricionales;"
```

## 7. La colección de Postman

`postman/ms-plan-nutricional.postman_collection.json` cubre los mismos flujos con
`pm.test`, para ejecutarlos contra la API levantada de verdad:

```bash
uv run fastapi dev main.py
newman run postman/ms-plan-nutricional.postman_collection.json \
       -e postman/ms-plan-nutricional.postman_environment.json
```

- Dos carpetas: `01 — Flujo correcto` (peticiones **dependientes**, se ejecutan en
  orden; la primera guarda `plan_id` en una variable de colección) y
  `02 — Flujo incorrecto`.
- Cada corrida genera un `paciente_id` nuevo con `{{$guid}}` para ser repetible.
- **Postman sí escribe en la base**: va por la red y no puede envolverse en una
  transacción. Es el precio de probar el servicio tal como está desplegado.

**Si cambias un endpoint, actualiza los dos sitios**: los tests de pytest y la
colección. Un endpoint cubierto solo en uno de los dos es deuda.

## 8. Errores frecuentes

- **Meter un mock** → si aparece un `AsyncMock`, no es una prueba de integración.
  Cámbiala de carpeta o quita el mock.
- **Asumir la base vacía** (`assert respuesta.json() == []` sobre `GET /planes`)
  → falla en cuanto alguien tenga datos de desarrollo. Acota por `paciente_id`.
- **Añadir `TRUNCATE` "para limpiar"** → rompe la garantía del entorno y borra
  datos reales del compañero. El rollback ya limpia.
- **Verificar solo el status** y no el código `tipo` → deja pasar el error
  equivocado con el mismo status.
- **Olvidar que el `PATCH`/`POST` devuelve 204** → no intentes leer JSON de la
  respuesta; verifica con un `GET`.
- **Reutilizar el `engine` de `database.py`** → es el de la app, con su propio
  pool. Usa la fixture `motor_test`.
- **`TestClient` síncrono** → el proyecto es async: `httpx.AsyncClient` con
  `ASGITransport`.
