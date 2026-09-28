"""Pruebas del caso de uso `EliminarRecetaUseCase`."""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import EliminarRecetaCommand
from plan_nutricional.application.use_cases.eliminar_receta import EliminarRecetaUseCase
from plan_nutricional.domain.exceptions import (
    PlanNoEncontradoError,
    RecetaNoEncontradaError,
    TiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model import TipoTiempoComida


def _plan_con_receta(construir_plan):
    """Plan con día 1, DESAYUNO y una receta dentro. Devuelve (plan, receta)."""
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    receta = plan.agregar_receta(
        numero_dia=1,
        tipo=TipoTiempoComida.DESAYUNO,
        nombre="Avena con frutas",
        descripcion="Desayuno alto en fibra",
        instrucciones="Mezclar y servir.",
        cantidad=Decimal("250"),
        unidad="g",
    )
    return plan, receta


async def test_eliminar_una_receta_existente_la_quita_del_tiempo_y_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan, receta = _plan_con_receta(construir_plan)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarRecetaUseCase(plan_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        EliminarRecetaCommand(
            plan_id=plan.id,
            numero_dia=1,
            tipo=TipoTiempoComida.DESAYUNO,
            receta_id=receta.id,
        )
    )

    # Assert
    assert plan.dias[0].tiempos_comida[0].recetas == []
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_eliminar_una_receta_de_un_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = EliminarRecetaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarRecetaCommand(
                plan_id=uuid4(),
                numero_dia=1,
                tipo=TipoTiempoComida.DESAYUNO,
                receta_id=uuid4(),
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_una_receta_de_un_tiempo_de_comida_inexistente_propaga_el_error(
    plan_repo_mock, construir_plan
):
    # Arrange — la receta está en DESAYUNO, se pide borrarla de CENA
    plan, receta = _plan_con_receta(construir_plan)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarRecetaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(TiempoComidaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarRecetaCommand(
                plan_id=plan.id,
                numero_dia=1,
                tipo=TipoTiempoComida.CENA,
                receta_id=receta.id,
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_una_receta_que_no_existe_propaga_el_error_del_dominio(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan, _ = _plan_con_receta(construir_plan)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarRecetaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(RecetaNoEncontradaError):
        await caso_de_uso.ejecutar(
            EliminarRecetaCommand(
                plan_id=plan.id,
                numero_dia=1,
                tipo=TipoTiempoComida.DESAYUNO,
                receta_id=uuid4(),
            )
        )

    assert len(plan.dias[0].tiempos_comida[0].recetas) == 1
    plan_repo_mock.guardar.assert_not_awaited()
