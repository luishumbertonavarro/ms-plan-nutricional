"""Pruebas del caso de uso `CrearPlanUseCase`.

Particularidad: este caso de uso no recupera nada del repositorio, solo construye
el agregado y lo guarda. Para inspeccionar lo que se guardó se usa
`plan_repo_mock.guardar.await_args.args[0]`, que devuelve el primer argumento
posicional con el que se llamó al mock.
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import (
    CrearPlanCommand,
    NecesidadNutricionalData,
)
from plan_nutricional.application.use_cases.crear_plan import CrearPlanUseCase
from plan_nutricional.domain.model import EstadoPlan


@pytest.fixture
def necesidad_data() -> NecesidadNutricionalData:
    return NecesidadNutricionalData(
        calorias=Decimal("2000"),
        proteinas=Decimal("120"),
        grasas=Decimal("60"),
        carbohidratos=Decimal("250"),
    )


async def test_crear_plan_guarda_un_plan_activo_con_los_datos_del_comando(
    plan_repo_mock, necesidad_data
):
    # Arrange
    paciente_id = uuid4()
    caso_de_uso = CrearPlanUseCase(plan_repo_mock)
    cmd = CrearPlanCommand(
        paciente_id=paciente_id,
        fecha_inicio=date(2026, 1, 1),
        duracion_dias=30,
        necesidad=necesidad_data,
        recomendacion_texto="Dieta hipocalórica",
    )

    # Act
    plan = await caso_de_uso.ejecutar(cmd)

    # Assert — el plan devuelto es exactamente el que se persistió
    plan_repo_mock.guardar.assert_awaited_once()
    plan_guardado = plan_repo_mock.guardar.await_args.args[0]
    assert plan_guardado is plan
    assert plan_guardado.paciente_id == paciente_id
    assert plan_guardado.estado is EstadoPlan.ACTIVO
    assert plan_guardado.duracion.dias == 30
    assert plan_guardado.fecha_fin == date(2026, 1, 30)


@pytest.mark.parametrize("duracion_invalida", [7, 0, 45])
async def test_crear_plan_con_duracion_no_permitida_no_persiste_nada(
    plan_repo_mock, necesidad_data, duracion_invalida
):
    # Arrange
    caso_de_uso = CrearPlanUseCase(plan_repo_mock)
    cmd = CrearPlanCommand(
        paciente_id=uuid4(),
        fecha_inicio=date(2026, 1, 1),
        duracion_dias=duracion_invalida,
        necesidad=necesidad_data,
        recomendacion_texto="Dieta hipocalórica",
    )

    # Act / Assert — falla al construir el Value Object DuracionPlan
    with pytest.raises(ValueError, match="15 o 30 días"):
        await caso_de_uso.ejecutar(cmd)

    plan_repo_mock.guardar.assert_not_awaited()


async def test_crear_plan_con_recomendacion_vacia_no_persiste_nada(
    plan_repo_mock, necesidad_data
):
    # Arrange
    caso_de_uso = CrearPlanUseCase(plan_repo_mock)
    cmd = CrearPlanCommand(
        paciente_id=uuid4(),
        fecha_inicio=date(2026, 1, 1),
        duracion_dias=15,
        necesidad=necesidad_data,
        recomendacion_texto="   ",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="no puede estar vacía"):
        await caso_de_uso.ejecutar(cmd)

    plan_repo_mock.guardar.assert_not_awaited()


async def test_crear_plan_con_macronutriente_negativo_no_persiste_nada(plan_repo_mock):
    # Arrange
    caso_de_uso = CrearPlanUseCase(plan_repo_mock)
    cmd = CrearPlanCommand(
        paciente_id=uuid4(),
        fecha_inicio=date(2026, 1, 1),
        duracion_dias=15,
        necesidad=NecesidadNutricionalData(
            calorias=Decimal("-100"),
            proteinas=Decimal("120"),
            grasas=Decimal("60"),
            carbohidratos=Decimal("250"),
        ),
        recomendacion_texto="Dieta hipocalórica",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="calorias"):
        await caso_de_uso.ejecutar(cmd)

    plan_repo_mock.guardar.assert_not_awaited()
