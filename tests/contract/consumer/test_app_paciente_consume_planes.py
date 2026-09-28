"""Contrato consumer: `app-paciente` → `ms-plan-nutricional`.

Cada test declara una interacción (petición + respuesta esperada), la ejercita con
el `ClientePlanes` real contra el mock server de Pact y la agrega a
`pacts/app-paciente-ms-plan-nutricional.json`.

El provider verifica este archivo en
`tests/contract/provider/test_verificar_planes_provider.py`.

Los valores concretos son solo ejemplos: los matchers (`match.*`) indican que el
provider debe devolver **ese tipo y esa forma**, no ese valor exacto.
"""
from uuid import UUID

import pytest
from pact import Pact, match

from tests.contract.conftest import contrato_limpio, mock_server
from tests.contract.consumer.cliente_planes import ClientePlanes, PlanNoEncontrado

pytestmark = pytest.mark.contract

CONSUMER = "app-paciente"
PROVIDER = "ms-plan-nutricional"

# Identificadores fijos: el provider los recibe como parámetros del estado.
PLAN_ID = "11111111-1111-4111-8111-111111111111"
PACIENTE_ID = "22222222-2222-4222-8222-222222222222"
PLAN_INEXISTENTE_ID = "99999999-9999-4999-8999-999999999999"

DECIMAL = r"^\d+(\.\d+)?$"
ESTADO = r"^(ACTIVO|FINALIZADO|CANCELADO)$"
TIPO_TIEMPO = r"^(DESAYUNO|MEDIA_MANANA|ALMUERZO|MERIENDA|CENA|MEDIA_NOCHE)$"


def plan_esperado(plan_id: str, paciente_id: str) -> dict:
    """Forma de `PlanResponse` que la app necesita para pintar el plan."""
    return {
        "id": match.uuid(plan_id),
        "paciente_id": match.uuid(paciente_id),
        "fecha_inicio": match.date("2026-01-01", "%Y-%m-%d"),
        "fecha_fin": match.date("2026-01-15", "%Y-%m-%d"),
        "estado": match.regex("ACTIVO", regex=ESTADO),
        "duracion_dias": match.integer(15),
        "necesidad": {
            "calorias": match.regex("2000.00", regex=DECIMAL),
            "proteinas": match.regex("120.00", regex=DECIMAL),
            "grasas": match.regex("60.00", regex=DECIMAL),
            "carbohidratos": match.regex("250.00", regex=DECIMAL),
        },
        "recomendacion_texto": match.string("Evitar azúcares refinados"),
        "dias": match.each_like(
            {
                "id": match.uuid(),
                "numero_dia": match.integer(1),
                "tiempos_comida": match.each_like(
                    {
                        "id": match.uuid(),
                        "tipo": match.regex("DESAYUNO", regex=TIPO_TIEMPO),
                        "recetas": match.each_like(
                            {
                                "id": match.uuid(),
                                "nombre": match.string("Avena con frutas"),
                                "descripcion": match.string("Desayuno alto en fibra"),
                                "instrucciones": match.string("Cocer la avena 5 minutos"),
                                "cantidad": match.regex("200.00", regex=DECIMAL),
                                "unidad": match.string("gr"),
                            }
                        ),
                    }
                ),
            }
        ),
    }


@pytest.fixture(scope="module", autouse=True)
def _regenerar_contrato(carpeta_pacts):
    contrato_limpio(carpeta_pacts, CONSUMER, PROVIDER)


@pytest.fixture
def pact(carpeta_pacts):
    pact = Pact(CONSUMER, PROVIDER).with_specification("V4")
    yield pact
    pact.write_file(carpeta_pacts, overwrite=False)


async def test_obtener_plan_existente_devuelve_el_plan_con_su_estructura(pact):
    # Arrange
    (
        pact.upon_receiving("una petición para obtener un plan existente")
        .given("existe un plan activo", plan_id=PLAN_ID, paciente_id=PACIENTE_ID)
        .with_request("GET", f"/planes/{PLAN_ID}")
        .with_header("Accept", "application/json")
        .will_respond_with(200)
        .with_body(plan_esperado(PLAN_ID, PACIENTE_ID), content_type="application/json")
    )

    with mock_server(pact) as servidor:
        # Act
        plan = await ClientePlanes(servidor.url).obtener_plan(UUID(PLAN_ID))

    # Assert
    assert plan["id"] == PLAN_ID
    assert plan["estado"] == "ACTIVO"
    assert plan["dias"][0]["tiempos_comida"][0]["recetas"][0]["nombre"]


async def test_obtener_planes_de_un_paciente_devuelve_la_lista_de_sus_planes(pact):
    # Arrange
    (
        pact.upon_receiving("una petición para listar los planes de un paciente")
        .given("existe un plan activo", plan_id=PLAN_ID, paciente_id=PACIENTE_ID)
        .with_request("GET", f"/planes/paciente/{PACIENTE_ID}")
        .with_header("Accept", "application/json")
        .will_respond_with(200)
        .with_body(
            match.each_like(plan_esperado(PLAN_ID, PACIENTE_ID), min=1),
            content_type="application/json",
        )
    )

    with mock_server(pact) as servidor:
        # Act
        planes = await ClientePlanes(servidor.url).obtener_planes_paciente(UUID(PACIENTE_ID))

    # Assert
    assert len(planes) >= 1
    assert all(p["paciente_id"] == PACIENTE_ID for p in planes)


async def test_obtener_plan_inexistente_lanza_plan_no_encontrado(pact):
    # Arrange
    (
        pact.upon_receiving("una petición para obtener un plan que no existe")
        .given("no existe el plan", plan_id=PLAN_INEXISTENTE_ID)
        .with_request("GET", f"/planes/{PLAN_INEXISTENTE_ID}")
        .with_header("Accept", "application/json")
        .will_respond_with(404)
        .with_body({"detail": match.string("Plan nutricional no encontrado.")}, content_type="application/json")
    )

    with mock_server(pact) as servidor:
        # Act / Assert
        with pytest.raises(PlanNoEncontrado):
            await ClientePlanes(servidor.url).obtener_plan(UUID(PLAN_INEXISTENTE_ID))
