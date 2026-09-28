"""Pruebas del caso de uso `EliminarDiaUseCase`.

Sigue el patrón de referencia de `test_agregar_dia.py`: el repositorio real se
sustituye por `AsyncMock(spec=PlanNutricionalRepository)` (fixture
`plan_repo_mock`), de modo que el test controla qué plan se recupera y verifica
que la persistencia solo ocurre cuando corresponde.
"""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import EliminarDiaCommand
from plan_nutricional.application.use_cases.eliminar_dia import EliminarDiaUseCase
from plan_nutricional.domain.exceptions import (
    DiaNoEncontradoError,
    PlanNoEncontradoError,
    PlanNoModificableError,
)
from plan_nutricional.domain.model import EstadoPlan


async def test_eliminar_un_dia_existente_lo_quita_del_plan_y_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1, 2])
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarDiaUseCase(plan_repo_mock)

    # Act
    await caso_de_uso.ejecutar(EliminarDiaCommand(plan_id=plan.id, numero_dia=1))

    # Assert
    assert plan.total_dias_agregados == 1
    assert [d.numero_dia for d in plan.dias] == [2]
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_eliminar_un_dia_de_un_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange — devolver None es la forma de simular "el plan no existe"
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = EliminarDiaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(EliminarDiaCommand(plan_id=uuid4(), numero_dia=1))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_dia_que_no_esta_agregado_propaga_el_error_del_dominio(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1])
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarDiaUseCase(plan_repo_mock)

    # Act / Assert — la regla la impone el agregado, no el caso de uso
    with pytest.raises(DiaNoEncontradoError):
        await caso_de_uso.ejecutar(EliminarDiaCommand(plan_id=plan.id, numero_dia=7))

    plan_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_dia_de_un_plan_finalizado_no_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(dias=[1], estado=EstadoPlan.FINALIZADO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = EliminarDiaUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoModificableError):
        await caso_de_uso.ejecutar(EliminarDiaCommand(plan_id=plan.id, numero_dia=1))

    assert plan.total_dias_agregados == 1
    plan_repo_mock.guardar.assert_not_awaited()
