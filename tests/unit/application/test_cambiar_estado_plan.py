"""Pruebas del caso de uso `CambiarEstadoPlanUseCase`.

Los mocks son especialmente útiles aquí: permiten comprobar que ante una
transición inválida **no se persiste nada**, es decir, que no queda un estado
parcialmente aplicado en la base de datos.
"""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import CambiarEstadoPlanCommand
from plan_nutricional.application.use_cases.cambiar_estado_plan import (
    CambiarEstadoPlanUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlanNoEncontradoError,
    TransicionEstadoInvalidaError,
)
from plan_nutricional.domain.model import EstadoPlan


@pytest.mark.parametrize(
    "estado_destino", [EstadoPlan.FINALIZADO, EstadoPlan.CANCELADO]
)
async def test_cambiar_estado_desde_activo_persiste_el_plan(
    plan_repo_mock, construir_plan, estado_destino
):
    # Arrange
    plan = construir_plan()
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = CambiarEstadoPlanUseCase(plan_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        CambiarEstadoPlanCommand(plan_id=plan.id, nuevo_estado=estado_destino)
    )

    # Assert
    assert plan.estado is estado_destino
    plan_repo_mock.obtener_por_id.assert_awaited_once_with(plan.id)
    plan_repo_mock.guardar.assert_awaited_once_with(plan)


async def test_cambiar_estado_de_plan_inexistente_lanza_error_y_no_persiste(
    plan_repo_mock,
):
    # Arrange
    plan_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = CambiarEstadoPlanUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(PlanNoEncontradoError):
        await caso_de_uso.ejecutar(
            CambiarEstadoPlanCommand(
                plan_id=uuid4(), nuevo_estado=EstadoPlan.FINALIZADO
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()


async def test_reactivar_un_plan_finalizado_lanza_error_y_no_persiste(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(estado=EstadoPlan.FINALIZADO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = CambiarEstadoPlanUseCase(plan_repo_mock)

    # Act / Assert — FINALIZADO es un estado terminal
    with pytest.raises(TransicionEstadoInvalidaError):
        await caso_de_uso.ejecutar(
            CambiarEstadoPlanCommand(plan_id=plan.id, nuevo_estado=EstadoPlan.ACTIVO)
        )

    assert plan.estado is EstadoPlan.FINALIZADO
    plan_repo_mock.guardar.assert_not_awaited()


async def test_finalizar_dos_veces_el_mismo_plan_lanza_error(
    plan_repo_mock, construir_plan
):
    # Arrange
    plan = construir_plan(estado=EstadoPlan.FINALIZADO)
    plan_repo_mock.obtener_por_id.return_value = plan
    caso_de_uso = CambiarEstadoPlanUseCase(plan_repo_mock)

    # Act / Assert
    with pytest.raises(TransicionEstadoInvalidaError):
        await caso_de_uso.ejecutar(
            CambiarEstadoPlanCommand(
                plan_id=plan.id, nuevo_estado=EstadoPlan.FINALIZADO
            )
        )

    plan_repo_mock.guardar.assert_not_awaited()
