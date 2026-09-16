---
name: contract-testing-plan-nutricional
description: Convenciones de contract testing con Pact (pact-python v3) en ms-plan-nutricional — roles consumer/provider, mapa de relaciones entre microservicios, matchers, provider states con SAVEPOINT sobre PostgreSQL, plantillas de interacción y problemas conocidos en Windows. Úsala al escribir, revisar o depurar cualquier archivo de tests/contract/ o pacts/, o al crear un adaptador HTTP hacia otro microservicio.
---

# Contract testing con Pact — ms-plan-nutricional

Complementa `testing-plan-nutricional` (unitarias) e
`integration-testing-plan-nutricional` (integración).

## 1. Conceptos

| Concepto | Qué es | Dónde está |
|---|---|---|
| **Consumer** | Servicio que hace la petición. **Escribe** el contrato. | `tests/contract/consumer/` |
| **Provider** | Servicio que responde. **Verifica** el contrato. | `tests/contract/provider/` |
| **Interacción** | Una pareja petición → respuesta esperada. | `pact.upon_receiving(...)` |
| **Pact file** | JSON con todas las interacciones de una relación. | `pacts/<consumer>-<provider>.json` |
| **Mock server** | Servidor falso que Pact levanta para el consumer. | `mock_server(pact)` |
| **Provider state** | Precondición de la interacción. | `.given("...", param=...)` → `HANDLERS` |
| **Matcher** | Regla de tipo o forma, en vez de un valor exacto. | `from pact import match` |
| **Verificación** | Pact reproduce el contrato contra la API real. | `Verifier(...).verify()` |

**Contract, integración o unitaria:**

- **Contract:** la forma del mensaje entre dos servicios (campos, tipos, status).
- **Integración:** el cableado interno (ORM, errores → HTTP, commit/rollback).
- **Unitaria:** las reglas de negocio.

## 2. Mapa de relaciones

```
app-paciente ────────────▶ ms-plan-nutricional     pacts/app-paciente-ms-plan-nutricional.json
  (ClientePlanes)            GET /planes/{id}               ✅ verificado aquí
                             GET /planes/paciente/{id}
                             GET /planes/{id} → 404

ms-plan-nutricional ─────▶ ms-pacientes            pacts/ms-plan-nutricional-ms-pacientes.json
  (PacienteGatewayHttp)      GET /pacientes/{id}            ⏳ lo verifica el equipo de ms-pacientes
                             GET /pacientes/{id} → 404
```

## 3. Plantilla — test consumer

```python
import pytest
from pact import Pact, match

from tests.contract.conftest import contrato_limpio, mock_server

pytestmark = pytest.mark.contract

CONSUMER, PROVIDER = "app-paciente", "ms-plan-nutricional"


@pytest.fixture(scope="module", autouse=True)
def _regenerar_contrato(carpeta_pacts):
    contrato_limpio(carpeta_pacts, CONSUMER, PROVIDER)


@pytest.fixture
def pact(carpeta_pacts):
    pact = Pact(CONSUMER, PROVIDER).with_specification("V4")
    yield pact
    pact.write_file(carpeta_pacts, overwrite=False)   # se fusiona con las demás


async def test_<accion>_<condicion>_<resultado>(pact):
    # Arrange
    (
        pact.upon_receiving("descripción única de la interacción")
        .given("nombre del estado", plan_id=PLAN_ID)       # parámetros → handler
        .with_request("GET", f"/planes/{PLAN_ID}")
        .with_header("Accept", "application/json")
        .will_respond_with(200)
        .with_body({"id": match.uuid(PLAN_ID)}, content_type="application/json")
    )

    with mock_server(pact) as servidor:
        # Act — siempre con el cliente real
        resultado = await ClientePlanes(servidor.url).obtener_plan(UUID(PLAN_ID))

    # Assert
    assert resultado["id"] == PLAN_ID
```

### Matchers para los tipos de esta API

| Campo | Matcher |
|---|---|
| UUID | `match.uuid(valor)` |
| `date` | `match.date("2026-01-01", "%Y-%m-%d")` (formato **strftime**, no `yyyy-MM-dd`) |
| `Decimal` (sale como cadena, p. ej. `"2000.00"`) | `match.regex("2000.00", regex=r"^\d+(\.\d+)?$")` |
| Enum (`EstadoPlan`, `TipoTiempoComida`) | `match.regex("ACTIVO", regex=r"^(ACTIVO\|FINALIZADO\|CANCELADO)$")` |
| `int` | `match.integer(15)` |
| `str` | `match.string("texto")` |
| Lista | `match.each_like(elemento, min=1)` |

## 4. Plantilla — provider state

En `tests/contract/provider/app_provider.py`:

```python
async def _nombre_del_estado(session: AsyncSession, params: dict) -> None:
    # Construye el agregado con los ids de `params` y guárdalo con el repositorio real.
    await PlanNutricionalRepositoryImpl(session).guardar(plan)

HANDLERS = {
    ...,
    "nombre del estado": _nombre_del_estado,   # mismo texto exacto que en given(...)
}
```

Cómo funciona el aislamiento, en tres capas:

1. **Transacción externa** abierta en el `lifespan` y revertida al apagar uvicorn.
2. **SAVEPOINT por interacción:** `begin_nested()` en el `setup` y `rollback()` en el
   `teardown`. Por eso dos interacciones pueden crear el mismo `plan_id`.
3. **Sesiones de la app** con `join_transaction_mode="create_savepoint"`: su
   `commit()` no confirma nada.

La app de verificación **monta la app real** (`provider.mount("/", app_real)`). La
ruta `/_pact/provider-states` solo existe ahí.

Para verificar un pact nuevo en el que nosotros somos provider, añádelo a
`CONTRATOS_VERIFICADOS` en `test_verificar_planes_provider.py`.

## 5. Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `Missing request` aunque el cliente recibió 200 | En Windows, el núcleo Rust registra la petición unos ms tarde. | Usa `mock_server(pact)`, que espera la coincidencia. |
| `Host mismatch: 127.0.0.1 != localhost` | `Verifier` usa `localhost` por defecto. | `Verifier(PROVIDER, host="127.0.0.1")` |
| `Expected '2026-01-01' to match a date pattern of ''yyyy-MM-dd''` | `match.date` espera formato strftime. | `"%Y-%m-%d"` |
| `Provider state sin handler` (400) | El texto del `given` no coincide con la clave de `HANDLERS`. | Copia el texto exacto. |
| `duplicate key` en la verificación | Un handler se ejecutó sin su SAVEPOINT. | No saltes el `begin_nested()` de `cambiar_estado`. |
| Interacciones fantasma en el pact | Quedó un pact viejo. | `contrato_limpio` al inicio de cada módulo consumer. |

## 6. Comandos

```powershell
docker compose -f ms-plan-nutricional-docker-compose.yml up -d
uv run pytest tests/contract/consumer -v                      # genera pacts/
uv run pytest tests/contract/provider -v                      # verifica (requiere PostgreSQL)
uv run pytest tests/contract/test_convenciones_contrato.py -v # guardián, sin Docker
uv run pytest -m contract                                     # solo contratos
```

El guardián `test_convenciones_contrato.py` comprueba automáticamente las reglas
de esta skill. Si te estorba, es que estás rompiendo una regla.
