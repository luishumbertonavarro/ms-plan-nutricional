"""Pruebas del caso de uso `AgregarRecetaUseCase` (receta escrita a mano).

Es el hermano de `test_agregar_receta_desde_catalogo.py`: aquí la receta no
viene del catálogo, sino que el nutricionista la escribe directamente, así que
el caso de uso trabaja con un único repositorio.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import AgregarRecetaCommand
from plan_nutricional.application.use_cases.agregar_receta import AgregarRecetaUseCase
from plan_nutricional.domain.exceptions import (
    PlanNoEncontradoError,
    RecetaDuplicadaError,
    TiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model import TipoTiempoComida


def _comando(plan_id, nombre: str = "Avena con frutas") -> AgregarRecetaCommand:
    """Comando de referencia; los tests solo varían el plan y el nombre."""
    return AgregarRecetaCommand(
        plan_id=plan_id,
        numero_dia=1,
        tipo=TipoTiempoComida.DESAYUNO,
        nombre=nombre,
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar la avena con la fruta picada y servir.",
        cantidad=Decimal("250"),
        unidad="g",
    )


async def test_agregar_una_receta_valida_la_devuelve_con_su_porcion_y_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarRecetaUseCase(plan_repo_mock)

    # Act
    receta = await caso_de_uso.ejecutar(_comando(plan.id))

    # Assert
    assert receta.nombre == "Avena con frutas"
    assert receta.porcion.cantidad == Decimal("250")
    assert receta.porcion.unidad == "g"
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_agregar_una_receta_a_un_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = AgregarRecetaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(_comando(uuid4()))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_agregar_una_receta_a_un_tiempo_de_comida_no_agregado_propaga_el_error(
    plan_repo_mock, construir_plan
):
    # Arrange — el día 1 existe, pero no se ha creado el DESAYUNO
    plan = construir_plan(dias=[1])
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarRecetaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(TiempoComidaNoEncontradoError):
        await caso_de_uso.ejecutar(_comando(plan.id))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_agregar_una_receta_con_el_mismo_nombre_en_otra_capitalizacion_es_duplicada(
    plan_repo_mock, construir_plan
):
    # Arrange — la comparación de nombres del dominio ignora mayúsculas
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarRecetaUseCase(plan_repo_mock)
    await caso_de_uso.ejecutar(_comando(plan.id, nombre="Avena con frutas"))
    plan_repo_mock.guardar.reset_mock()

    # Act / Assert
    with pytest.raises(RecetaDuplicadaError):
        await caso_de_uso.ejecutar(_comando(plan.id, nombre="AVENA CON FRUTAS"))

    plan_repo_mock.guardar.assert_not_awaited()
