"""Pruebas del caso de uso `AgregarRecetaDesdeCatalogoUseCase`.

Es el caso de uso más rico del microservicio: recibe **dos** repositorios por
inyección y tiene tres ramas de error más una regla de valores por defecto.

Con dos mocks se puede verificar algo que de otro modo sería invisible: el
**corto-circuito**. Si el plan no existe, el caso de uso no debe llegar siquiera
a consultar el catálogo — se comprueba con `assert_not_awaited()` sobre el
segundo mock.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import (
    AgregarRecetaDesdeCatalogoCommand,
)
from plan_nutricional.application.use_cases.agregar_receta_desde_catalogo import (
    AgregarRecetaDesdeCatalogoUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlanNoEncontradoError,
    RecetaCatalogoInactivaError,
    RecetaCatalogoNoEncontradaError,
)
from plan_nutricional.domain.model import TipoTiempoComida


@pytest.fixture
def plan_con_desayuno(construir_plan):
    """Plan de 15 días con el día 1 y su desayuno ya creados."""
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    return plan


@pytest.fixture
def caso_de_uso(plan_repo_mock, catalogo_repo_mock):
    return AgregarRecetaDesdeCatalogoUseCase(plan_repo_mock, catalogo_repo_mock)


def construir_comando(plan_id, receta_catalogo_id, cantidad=None, unidad=None):
    return AgregarRecetaDesdeCatalogoCommand(
        plan_id=plan_id,
        numero_dia=1,
        tipo=TipoTiempoComida.DESAYUNO,
        receta_catalogo_id=receta_catalogo_id,
        cantidad=cantidad,
        unidad=unidad,
    )


# ---------------------------------------------------------------------------
# Camino feliz y regla de valores por defecto
# ---------------------------------------------------------------------------

async def test_sin_cantidad_ni_unidad_usa_la_porcion_por_defecto_del_catalogo(
    caso_de_uso, plan_repo_mock, catalogo_repo_mock, plan_con_desayuno, receta_catalogo
):
    # Arrange — la receta del catálogo trae porción por defecto de 250 g
    plan_repo_mock.obtener_por_id.return_value = plan_con_desayuno
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo

    # Act
    receta = await caso_de_uso.ejecutar(
        construir_comando(plan_con_desayuno.id, receta_catalogo.id)
    )

    # Assert
    assert receta.nombre == receta_catalogo.nombre
    assert receta.porcion.cantidad == Decimal("250")
    assert receta.porcion.unidad == "g"
    plan_repo_mock.guardar.assert_awaited_once_with(plan_con_desayuno)


async def test_la_cantidad_del_comando_tiene_prioridad_sobre_la_del_catalogo(
    caso_de_uso, plan_repo_mock, catalogo_repo_mock, plan_con_desayuno, receta_catalogo
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = plan_con_desayuno
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo

    # Act
    receta = await caso_de_uso.ejecutar(
        construir_comando(
            plan_con_desayuno.id,
            receta_catalogo.id,
            cantidad=Decimal("100"),
            unidad="ml",
        )
    )

    # Assert — el comando gana; el default del catálogo (250 g) se ignora
    assert receta.porcion.cantidad == Decimal("100")
    assert receta.porcion.unidad == "ml"


async def test_consulta_ambos_repositorios_con_los_identificadores_del_comando(
    caso_de_uso, plan_repo_mock, catalogo_repo_mock, plan_con_desayuno, receta_catalogo
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = plan_con_desayuno
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo

    # Act
    await caso_de_uso.ejecutar(
        construir_comando(plan_con_desayuno.id, receta_catalogo.id)
    )

    # Assert — cada mock recibió exactamente el id que le corresponde
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan_con_desayuno.id)
    catalogo_repo_mock.obtener_por_id.assert_awaited_once_with(receta_catalogo.id)


# ---------------------------------------------------------------------------
# Las tres ramas de error
# ---------------------------------------------------------------------------

async def test_plan_inexistente_corta_antes_de_consultar_el_catalogo(
    caso_de_uso, plan_repo_mock, catalogo_repo_mock
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(construir_comando(uuid4(), uuid4()))

    # El corto-circuito: ni se consultó el catálogo ni se guardó nada
    catalogo_repo_mock.obtener_por_id.assert_not_awaited()
    plan_repo_mock.guardar.assert_not_awaited()


async def test_receta_de_catalogo_inexistente_lanza_error_y_no_persiste(
    caso_de_uso, plan_repo_mock, catalogo_repo_mock, plan_con_desayuno
):
    # Arrange — el plan sí existe, la receta del catálogo no
    plan_repo_mock.obtener_por_id.return_value = plan_con_desayuno
    catalogo_repo_mock.obtener_por_id.return_value = None

    # Act / Assert
    with pytest.raises(RecetaCatalogoNoEncontradaError):
        await caso_de_uso.ejecutar(construir_comando(plan_con_desayuno.id, uuid4()))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_receta_de_catalogo_inactiva_lanza_error_y_no_persiste(
    caso_de_uso, plan_repo_mock, catalogo_repo_mock, plan_con_desayuno, receta_catalogo
):
    # Arrange — una receta desactivada no puede usarse en planes nuevos
    receta_catalogo.desactivar()
    plan_repo_mock.obtener_por_id.return_value = plan_con_desayuno
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo

    # Act / Assert
    with pytest.raises(RecetaCatalogoInactivaError):
        await caso_de_uso.ejecutar(
            construir_comando(plan_con_desayuno.id, receta_catalogo.id)
        )

    plan_repo_mock.guardar.assert_not_awaited()
