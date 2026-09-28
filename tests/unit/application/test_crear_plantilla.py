"""Pruebas del caso de uso `CrearPlantillaUseCase`.

A diferencia del plan de un paciente, la plantilla no tiene ciclo de vida: es
siempre editable. Lo único que valida al crearse es el nombre y la duración.
"""

import pytest

from plan_nutricional.application.commands.commands import CrearPlantillaCommand
from plan_nutricional.application.use_cases.crear_plantilla import CrearPlantillaUseCase


async def test_crear_una_plantilla_valida_la_devuelve_vacia_y_la_persiste(
    plantilla_repo_mock,
):
    # Arrange
    caso_de_uso = CrearPlantillaUseCase(plantilla_repo_mock)
    comando = CrearPlantillaCommand(
        nombre="Plantilla hipocalórica",
        descripcion="Base de 15 días para pacientes con sobrepeso",
        duracion_dias=15,
    )

    # Act
    plantilla = await caso_de_uso.ejecutar(comando)

    # Assert
    assert plantilla.nombre == "Plantilla hipocalórica"
    assert plantilla.duracion.dias == 15
    assert plantilla.dias == []
    plantilla_repo_mock.guardar.assert_awaited_once_with(plantilla)


async def test_crear_una_plantilla_sin_nombre_no_persiste_nada(plantilla_repo_mock):
    # Arrange
    caso_de_uso = CrearPlantillaUseCase(plantilla_repo_mock)
    comando = CrearPlantillaCommand(nombre="  ", descripcion="Sin nombre", duracion_dias=15)

    # Act / Assert
    with pytest.raises(ValueError):
        await caso_de_uso.ejecutar(comando)

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_crear_una_plantilla_con_una_duracion_no_permitida_no_persiste_nada(
    plantilla_repo_mock,
):
    # Arrange — `DuracionPlan` solo admite 15 o 30 días
    caso_de_uso = CrearPlantillaUseCase(plantilla_repo_mock)
    comando = CrearPlantillaCommand(
        nombre="Plantilla de 20 días", descripcion="No permitida", duracion_dias=20
    )

    # Act / Assert
    with pytest.raises(ValueError):
        await caso_de_uso.ejecutar(comando)

    plantilla_repo_mock.guardar.assert_not_awaited()
