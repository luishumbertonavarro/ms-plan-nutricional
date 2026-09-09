"""Pruebas de integración del agregado PlanNutricional — flujos incorrectos.

Las pruebas unitarias ya comprueban que el dominio lanza la excepción correcta.
Lo que aquí se verifica es lo que ninguna de ellas puede ver:

1. Que `presentation/api/exception_handlers.py` traduce cada excepción de dominio
   al **status HTTP y al código `tipo`** que promete el README.
2. Que tras un error **no queda nada escrito** en la base — es decir, que el
   `rollback` de `get_db_session` funciona de verdad. Es el equivalente
   integrado del `plan_repo_mock.guardar.assert_not_awaited()` de las unitarias.
"""

from uuid import uuid4

import pytest

from tests.integration.test_planes_api_flujo_correcto import cuerpo_plan

pytestmark = pytest.mark.integration


async def _crear_plan(cliente, duracion_dias: int = 15) -> str:
    """Crea un plan válido y devuelve su id."""
    respuesta = await cliente.post("/planes", json=cuerpo_plan(str(uuid4()), duracion_dias))
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


# ---------------------------------------------------------------------------
# 404 — recursos que no existen
# ---------------------------------------------------------------------------

async def test_obtener_plan_inexistente_devuelve_404(cliente):
    # Arrange
    plan_id = uuid4()

    # Act
    respuesta = await cliente.get(f"/planes/{plan_id}")

    # Assert
    assert respuesta.status_code == 404
    assert "no encontrado" in respuesta.json()["detail"].lower()


async def test_agregar_dia_a_plan_inexistente_devuelve_404(cliente):
    # Arrange
    plan_id = uuid4()

    # Act
    respuesta = await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Assert
    assert respuesta.status_code == 404
    assert respuesta.json()["tipo"] == "PLAN_NO_ENCONTRADO"


async def test_agregar_tiempo_comida_a_dia_inexistente_devuelve_404(cliente):
    # Arrange
    plan_id = await _crear_plan(cliente)

    # Act — el día 5 nunca se agregó al plan
    respuesta = await cliente.post(
        f"/planes/{plan_id}/dias/5/tiempos", json={"tipo": "CENA"}
    )

    # Assert
    assert respuesta.status_code == 404
    assert respuesta.json()["tipo"] == "DIA_NO_ENCONTRADO"


# ---------------------------------------------------------------------------
# 409 — conflictos con el estado actual del agregado
# ---------------------------------------------------------------------------

async def test_agregar_dia_duplicado_devuelve_409_y_no_lo_persiste(cliente):
    # Arrange
    plan_id = await _crear_plan(cliente)
    await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Act
    respuesta = await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Assert
    assert respuesta.status_code == 409
    assert respuesta.json()["tipo"] == "DIA_DUPLICADO"

    # El rollback debe haber dejado el plan tal como estaba: un solo día.
    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert len(plan["dias"]) == 1


async def test_agregar_tiempo_comida_duplicado_devuelve_409(cliente):
    # Arrange
    plan_id = await _crear_plan(cliente)
    await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})
    await cliente.post(f"/planes/{plan_id}/dias/1/tiempos", json={"tipo": "DESAYUNO"})

    # Act
    respuesta = await cliente.post(
        f"/planes/{plan_id}/dias/1/tiempos", json={"tipo": "DESAYUNO"}
    )

    # Assert
    assert respuesta.status_code == 409
    assert respuesta.json()["tipo"] == "TIEMPO_COMIDA_DUPLICADO"


async def test_agregar_receta_con_nombre_duplicado_ignorando_mayusculas_devuelve_409(cliente):
    """`TiempoComida.agregar_receta` compara nombres en minúsculas."""
    # Arrange
    plan_id = await _crear_plan(cliente)
    await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})
    await cliente.post(f"/planes/{plan_id}/dias/1/tiempos", json={"tipo": "DESAYUNO"})
    receta = {
        "nombre": "Avena con frutas",
        "descripcion": "Avena cocida con banana.",
        "instrucciones": "Cocer 5 minutos.",
        "cantidad": "250",
        "unidad": "gramos",
    }
    await cliente.post(f"/planes/{plan_id}/dias/1/tiempos/DESAYUNO/recetas", json=receta)

    # Act — mismo nombre en mayúsculas
    respuesta = await cliente.post(
        f"/planes/{plan_id}/dias/1/tiempos/DESAYUNO/recetas",
        json={**receta, "nombre": "AVENA CON FRUTAS"},
    )

    # Assert
    assert respuesta.status_code == 409
    assert respuesta.json()["tipo"] == "RECETA_DUPLICADA"

    # Y en la base sigue habiendo una sola receta.
    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert len(plan["dias"][0]["tiempos_comida"][0]["recetas"]) == 1


async def test_agregar_dia_a_plan_finalizado_devuelve_409(cliente):
    # Arrange
    plan_id = await _crear_plan(cliente)
    await cliente.patch(f"/planes/{plan_id}/estado", json={"nuevo_estado": "FINALIZADO"})

    # Act
    respuesta = await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Assert
    assert respuesta.status_code == 409
    assert respuesta.json()["tipo"] == "PLAN_NO_MODIFICABLE"

    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert plan["dias"] == []


async def test_reactivar_un_plan_finalizado_devuelve_409(cliente):
    """FINALIZADO es un estado terminal: no admite ninguna transición."""
    # Arrange
    plan_id = await _crear_plan(cliente)
    await cliente.patch(f"/planes/{plan_id}/estado", json={"nuevo_estado": "FINALIZADO"})

    # Act
    respuesta = await cliente.patch(
        f"/planes/{plan_id}/estado", json={"nuevo_estado": "ACTIVO"}
    )

    # Assert
    assert respuesta.status_code == 409
    assert respuesta.json()["tipo"] == "TRANSICION_ESTADO_INVALIDA"

    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert plan["estado"] == "FINALIZADO"


# ---------------------------------------------------------------------------
# 422 — datos que violan una regla de negocio o el contrato de la API
# ---------------------------------------------------------------------------

async def test_agregar_dia_fuera_de_la_duracion_devuelve_422(cliente):
    # Arrange
    plan_id = await _crear_plan(cliente, duracion_dias=15)

    # Act
    respuesta = await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 16})

    # Assert
    assert respuesta.status_code == 422
    assert respuesta.json()["tipo"] == "DIA_FUERA_DE_DURACION"

    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert plan["dias"] == []


async def test_crear_plan_con_duracion_no_permitida_devuelve_422(cliente):
    """`DuracionPlan` solo admite 15 o 30 días; el ValueError se mapea a 422."""
    # Arrange
    paciente_id = str(uuid4())
    cuerpo = cuerpo_plan(paciente_id, duracion_dias=20)

    # Act
    respuesta = await cliente.post("/planes", json=cuerpo)

    # Assert
    assert respuesta.status_code == 422
    assert respuesta.json()["tipo"] == "VALOR_INVALIDO"

    # Nada se guardó: el paciente sigue sin ningún plan.
    assert (await cliente.get(f"/planes/paciente/{paciente_id}")).json() == []


async def test_crear_plan_con_recomendacion_vacia_devuelve_422(cliente):
    # Arrange
    cuerpo = {**cuerpo_plan(str(uuid4())), "recomendacion_texto": "   "}

    # Act
    respuesta = await cliente.post("/planes", json=cuerpo)

    # Assert
    assert respuesta.status_code == 422
    assert respuesta.json()["tipo"] == "VALOR_INVALIDO"


async def test_crear_plan_sin_paciente_id_devuelve_422_de_validacion(cliente):
    """Este 422 no lo produce el dominio, sino la validación de Pydantic."""
    # Arrange
    cuerpo = cuerpo_plan(str(uuid4()))
    del cuerpo["paciente_id"]

    # Act
    respuesta = await cliente.post("/planes", json=cuerpo)

    # Assert
    assert respuesta.status_code == 422
    campos = [error["loc"][-1] for error in respuesta.json()["detail"]]
    assert "paciente_id" in campos


async def test_agregar_tiempo_comida_de_tipo_inexistente_devuelve_422(cliente):
    # Arrange
    plan_id = await _crear_plan(cliente)
    await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})

    # Act — "BRUNCH" no pertenece al enum TipoTiempoComida
    respuesta = await cliente.post(
        f"/planes/{plan_id}/dias/1/tiempos", json={"tipo": "BRUNCH"}
    )

    # Assert
    assert respuesta.status_code == 422
