"""Pruebas del caso de uso `AgregarTiempoComidaUseCase`.

El caso de uso no contiene reglas propias: recupera el plan, delega en el
agregado y persiste. Por eso los tests comprueban dos cosas distintas — que el
resultado es el esperado y que las excepciones del dominio llegan intactas al
llamador sin haber escrito nada.
"""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import AgregarTiempoComidaCommand
from plan_nutricional.application.use_cases.agregar_tiempo_comida import (
    AgregarTiempoComidaUseCase,
)
from plan_nutricional.domain.exceptions import (
    DiaNoEncontradoError,
    PlanNoEncontradoError,
    TiempoComidaDuplicadoError,
)
from plan_nutricional.domain.model import TipoTiempoComida


async def test_agregar_un_tiempo_de_comida_valido_lo_devuelve_y_persiste_el_plan(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1])
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarTiempoComidaUseCase(plan_repo_mock)

    # Act
    tiempo = await caso_de_uso.ejecutar(
        AgregarTiempoComidaCommand(
            plan_id=plan.id, numero_dia=1, tipo=TipoTiempoComida.DESAYUNO
        )
    )

    # Assert
    assert tiempo.tipo is TipoTiempoComida.DESAYUNO
    assert [t.tipo for t in plan.dias[0].tiempos_comida] == [TipoTiempoComida.DESAYUNO]
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_agregar_un_tiempo_de_comida_en_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = AgregarTiempoComidaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(
            AgregarTiempoComidaCommand(
                plan_id=uuid4(), numero_dia=1, tipo=TipoTiempoComida.ALMUERZO
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_agregar_un_tiempo_de_comida_en_un_dia_no_agregado_propaga_el_error(
    plan_repo_mock, construir_plan
):
    # Arrange — el plan existe, pero el día 5 nunca se agregó
    plan = construir_plan(dias=[1])
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarTiempoComidaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(DiaNoEncontradoError):
        await caso_de_uso.ejecutar(
            AgregarTiempoComidaCommand(
                plan_id=plan.id, numero_dia=5, tipo=TipoTiempoComida.CENA
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_agregar_dos_veces_el_mismo_tiempo_de_comida_lanza_duplicado_y_no_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange — el día ya tiene DESAYUNO
    plan = construir_plan(dias=[1])
    plan.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = AgregarTiempoComidaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(TiempoComidaDuplicadoError):
        await caso_de_uso.ejecutar(
            AgregarTiempoComidaCommand(
                plan_id=plan.id, numero_dia=1, tipo=TipoTiempoComida.DESAYUNO
            )
        )

    assert len(plan.dias[0].tiempos_comida) == 1
    plan_repo_mock.guardar.assert_not_awaited()
