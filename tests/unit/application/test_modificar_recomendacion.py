"""Pruebas del caso de uso `ModificarRecomendacionUseCase`.

La recomendación es un value object (`RecomendacionNutricional`): modificarla
significa **reemplazarlo** por otro, no mutarlo. El caso de uso solo orquesta.
"""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import ModificarRecomendacionCommand
from plan_nutricional.application.use_cases.modificar_recomendacion import (
    ModificarRecomendacionUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlanNoEncontradoError,
    PlanNoModificableError,
)
from plan_nutricional.domain.model import EstadoPlan


async def test_modificar_la_recomendacion_reemplaza_el_texto_y_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan()
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = ModificarRecomendacionUseCase(plan_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        ModificarRecomendacionCommand(plan_id=plan.id, texto="Aumentar la hidratación")
    )

    # Assert
    assert plan.recomendacion.texto == "Aumentar la hidratación"
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_modificar_la_recomendacion_de_un_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = ModificarRecomendacionUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(
            ModificarRecomendacionCommand(plan_id=uuid4(), texto="Da igual")
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_modificar_la_recomendacion_de_un_plan_finalizado_no_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(estado=EstadoPlan.FINALIZADO)
    texto_original = plan.recomendacion.texto
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = ModificarRecomendacionUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoModificableError):
        await caso_de_uso.ejecutar(
            ModificarRecomendacionCommand(plan_id=plan.id, texto="Otro texto")
        )

    assert plan.recomendacion.texto == texto_original
    plan_repo_mock.guardar.assert_not_awaited()
