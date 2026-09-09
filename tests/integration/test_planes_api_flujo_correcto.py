"""Pruebas de integración del agregado PlanNutricional — flujo correcto.

Lo que aquí se verifica no lo puede ver una prueba unitaria: que el estado
**sobrevive de una petición HTTP a la siguiente** porque de verdad se escribió en
PostgreSQL, y que el mapeo dominio ↔ ORM reconstruye la jerarquía completa
plan → día → tiempo de comida → receta.

Por eso el test principal es uno solo y largo: partirlo en pedazos rompería
justamente lo que se quiere demostrar, que es la continuidad del estado.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration

# Fecha fija, igual que en las pruebas unitarias: un test que dependa de "hoy"
# deja de ser determinista.
FECHA_INICIO = "2026-01-01"


def cuerpo_plan(paciente_id: str, duracion_dias: int = 15) -> dict:
    """Cuerpo válido de `POST /planes`."""
    return {
        "paciente_id": paciente_id,
        "fecha_inicio": FECHA_INICIO,
        "duracion_dias": duracion_dias,
        "necesidad": {
            "calorias": "2000",
            "proteinas": "120",
            "grasas": "60",
            "carbohidratos": "250",
        },
        "recomendacion_texto": "Dieta hipocalórica con alto aporte proteico.",
    }


async def test_ciclo_de_vida_completo_de_un_plan_persiste_en_la_base(cliente):
    """Recorre el plan de punta a punta: crearlo, poblarlo y cerrarlo.

    Cada paso es una petición HTTP independiente. Que el paso N vea lo que hizo
    el paso N-1 solo es posible si el repositorio escribió realmente en la base.
    """
    # Arrange
    paciente_id = str(uuid4())

    # Act / Assert — 1. Crear el plan
    respuesta = await cliente.post("/planes", json=cuerpo_plan(paciente_id))

    assert respuesta.status_code == 201
    plan = respuesta.json()
    plan_id = plan["id"]
    assert plan["paciente_id"] == paciente_id
    assert plan["estado"] == "ACTIVO"
    assert plan["duracion_dias"] == 15
    # fecha_fin la calcula el dominio: fecha_inicio + (duración - 1).
    assert plan["fecha_fin"] == "2026-01-15"
    assert plan["dias"] == []

    # Act / Assert — 2. Agregar un día
    respuesta = await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 1})
    assert respuesta.status_code == 204

    # Act / Assert — 3. Agregar un tiempo de comida a ese día
    respuesta = await cliente.post(
        f"/planes/{plan_id}/dias/1/tiempos", json={"tipo": "DESAYUNO"}
    )
    assert respuesta.status_code == 204

    # Act / Assert — 4. Agregar una receta a ese tiempo de comida
    respuesta = await cliente.post(
        f"/planes/{plan_id}/dias/1/tiempos/DESAYUNO/recetas",
        json={
            "nombre": "Avena con frutas",
            "descripcion": "Avena cocida con banana y frutos rojos.",
            "instrucciones": "Cocer la avena 5 minutos y añadir la fruta picada.",
            "cantidad": "250",
            "unidad": "gramos",
        },
    )
    assert respuesta.status_code == 204

    # Act / Assert — 5. Releer el plan: la jerarquía completa vuelve de la base
    respuesta = await cliente.get(f"/planes/{plan_id}")

    assert respuesta.status_code == 200
    plan = respuesta.json()
    assert len(plan["dias"]) == 1

    dia = plan["dias"][0]
    assert dia["numero_dia"] == 1
    assert len(dia["tiempos_comida"]) == 1

    tiempo = dia["tiempos_comida"][0]
    assert tiempo["tipo"] == "DESAYUNO"
    assert len(tiempo["recetas"]) == 1

    receta = tiempo["recetas"][0]
    assert receta["nombre"] == "Avena con frutas"
    assert receta["unidad"] == "gramos"
    # Numeric(10,3) en la base: el valor vuelve con la escala de la columna.
    assert Decimal(receta["cantidad"]) == Decimal("250")

    # Act / Assert — 6. Modificar la recomendación
    respuesta = await cliente.patch(
        f"/planes/{plan_id}/recomendacion",
        json={"texto": "Aumentar la ingesta de fibra."},
    )
    assert respuesta.status_code == 204

    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert plan["recomendacion_texto"] == "Aumentar la ingesta de fibra."

    # Act / Assert — 7. Finalizar el plan
    respuesta = await cliente.patch(
        f"/planes/{plan_id}/estado", json={"nuevo_estado": "FINALIZADO"}
    )
    assert respuesta.status_code == 204

    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert plan["estado"] == "FINALIZADO"
    # El día y su contenido siguen ahí tras el cambio de estado.
    assert len(plan["dias"]) == 1


async def test_eliminar_un_dia_lo_borra_tambien_de_la_base(cliente):
    """El DELETE debe propagarse a las filas hijas por la cascada del ORM."""
    # Arrange
    plan_id = (await cliente.post("/planes", json=cuerpo_plan(str(uuid4())))).json()["id"]
    await cliente.post(f"/planes/{plan_id}/dias", json={"numero_dia": 3})
    await cliente.post(f"/planes/{plan_id}/dias/3/tiempos", json={"tipo": "ALMUERZO"})

    # Act
    respuesta = await cliente.delete(f"/planes/{plan_id}/dias/3")

    # Assert
    assert respuesta.status_code == 204
    plan = (await cliente.get(f"/planes/{plan_id}")).json()
    assert plan["dias"] == []


async def test_listar_planes_activos_devuelve_solo_los_activos(cliente):
    # Arrange
    plan_activo_id = (await cliente.post("/planes", json=cuerpo_plan(str(uuid4())))).json()["id"]
    plan_finalizado_id = (
        await cliente.post("/planes", json=cuerpo_plan(str(uuid4())))
    ).json()["id"]
    await cliente.patch(
        f"/planes/{plan_finalizado_id}/estado", json={"nuevo_estado": "FINALIZADO"}
    )

    # Act
    respuesta = await cliente.get("/planes")

    # Assert — se comprueba pertenencia, no igualdad: el listado podría contener
    # planes preexistentes en la base de desarrollo y el test no debe asumir que
    # está vacía.
    assert respuesta.status_code == 200
    ids = [p["id"] for p in respuesta.json()]
    assert plan_activo_id in ids
    assert plan_finalizado_id not in ids


async def test_obtener_planes_de_un_paciente_devuelve_solo_los_suyos(cliente):
    # Arrange
    paciente_id = str(uuid4())
    otro_paciente_id = str(uuid4())
    plan_propio_id = (await cliente.post("/planes", json=cuerpo_plan(paciente_id))).json()["id"]
    await cliente.post("/planes", json=cuerpo_plan(otro_paciente_id))

    # Act
    respuesta = await cliente.get(f"/planes/paciente/{paciente_id}")

    # Assert
    assert respuesta.status_code == 200
    planes = respuesta.json()
    assert len(planes) == 1
    assert planes[0]["id"] == plan_propio_id


async def test_consultar_los_planes_de_un_paciente_sin_planes_devuelve_lista_vacia(cliente):
    # Arrange — un paciente que nunca tuvo un plan
    paciente_id = str(uuid4())

    # Act
    respuesta = await cliente.get(f"/planes/paciente/{paciente_id}")

    # Assert
    assert respuesta.status_code == 200
    assert respuesta.json() == []


async def test_crear_plan_de_treinta_dias_calcula_bien_la_fecha_fin(cliente):
    # Arrange
    cuerpo = cuerpo_plan(str(uuid4()), duracion_dias=30)

    # Act
    respuesta = await cliente.post("/planes", json=cuerpo)

    # Assert
    assert respuesta.status_code == 201
    plan = respuesta.json()
    assert plan["duracion_dias"] == 30
    assert plan["fecha_inicio"] == FECHA_INICIO
    assert plan["fecha_fin"] == str(date(2026, 1, 30))


# ---------------------------------------------------------------------------
# Aislamiento: los dos tests siguientes van en pareja
# ---------------------------------------------------------------------------

# Un paciente fijo compartido por los dos tests de abajo. El primero le crea un
# plan; el segundo comprueba que ya no existe.
PACIENTE_DE_PRUEBA_DE_AISLAMIENTO = "11111111-1111-1111-1111-111111111111"


async def test_aislamiento_paso_1_crea_un_plan_para_un_paciente_fijo(cliente):
    """Primera mitad de la demostración del aislamiento transaccional."""
    # Act
    respuesta = await cliente.post(
        "/planes", json=cuerpo_plan(PACIENTE_DE_PRUEBA_DE_AISLAMIENTO)
    )

    # Assert — dentro de este test el plan existe y se puede consultar
    assert respuesta.status_code == 201
    planes = (
        await cliente.get(f"/planes/paciente/{PACIENTE_DE_PRUEBA_DE_AISLAMIENTO}")
    ).json()
    assert len(planes) == 1


async def test_aislamiento_paso_2_el_plan_del_test_anterior_ya_no_existe(cliente):
    """Segunda mitad: el plan creado arriba desapareció al revertir la transacción.

    Es la prueba de que las pruebas de integración **no ensucian la base de
    datos**: cada test corre dentro de una transacción que se revierte al
    terminar (ver la fixture `cliente` en `conftest.py`).

    Ejecutado por separado este test también pasa, así que no introduce una
    dependencia real de orden.
    """
    # Act
    respuesta = await cliente.get(f"/planes/paciente/{PACIENTE_DE_PRUEBA_DE_AISLAMIENTO}")

    # Assert
    assert respuesta.status_code == 200
    assert respuesta.json() == []
