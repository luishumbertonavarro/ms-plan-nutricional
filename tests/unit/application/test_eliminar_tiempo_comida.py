"""Pruebas del caso de uso `EliminarTiempoComidaUseCase`."""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import EliminarTiempoComidaCommand
from plan_nutricional.application.use_cases.eliminar_tiempo_comida import (
    EliminarTiempoComidaUseCase,
)
from plan_nutricional.domain.exceptions import (
    DiaNoEncontradoError,
    PlanNoEncontradoError,
    TiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model import TipoTiempoComida


async def test_eliminar_un_tiempo_de_comida_existente_lo_quita_del_dia_y_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan.agregar_tiempo_comida(1, TipoTiempoComida.CENA)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarTiempoComidaUseCase(plan_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        EliminarTiempoComidaCommand(
            plan_id=plan.id, numero_dia=1, tipo=TipoTiempoComida.DESAYUNO
        )
    )

    # Assert
    assert [t.tipo for t in plan.dias[0].tiempos_comida] == [TipoTiempoComida.CENA]
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_eliminar_un_tiempo_de_comida_de_un_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = EliminarTiempoComidaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarTiempoComidaCommand(
                plan_id=uuid4(), numero_dia=1, tipo=TipoTiempoComida.DESAYUNO
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_tiempo_de_comida_de_un_dia_no_agregado_propaga_el_error(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1])
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarTiempoComidaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(DiaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarTiempoComidaCommand(
                plan_id=plan.id, numero_dia=9, tipo=TipoTiempoComida.DESAYUNO
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_tiempo_de_comida_que_el_dia_no_tiene_propaga_el_error(
    plan_repo_mock, construir_plan
):
    # Arrange — el día 1 existe pero solo tiene DESAYUNO
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarTiempoComidaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(TiempoComidaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarTiempoComidaCommand(
                plan_id=plan.id, numero_dia=1, tipo=TipoTiempoComida.MERIENDA
            )
        )

    assert len(plan.dias[0].tiempos_comida) == 1
    plan_repo_mock.guardar.assert_not_awaited()
