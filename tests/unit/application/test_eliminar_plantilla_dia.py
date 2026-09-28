"""Pruebas del caso de uso `EliminarPlantillaDiaUseCase`."""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import EliminarPlantillaDiaCommand
from plan_nutricional.application.use_cases.eliminar_plantilla_dia import (
    EliminarPlantillaDiaUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlantillaDiaNoEncontradoError,
    PlantillaNoEncontradaError,
)


async def test_eliminar_un_dia_existente_de_la_plantilla_lo_quita_y_persiste(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_dia(2)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        EliminarPlantillaDiaCommand(plantilla_id=plantilla.id, numero_dia=1)
    )

    # Assert
    assert [d.numero_dia for d in plantilla.dias] == [2]
    plantilla_repo_mock.obtener_por_id.assert_awaited_once_with(plantilla.id)
    plantilla_repo_mock.guardar.assert_awaited_once_with(plantilla)


async def test_eliminar_un_dia_de_una_plantilla_inexistente_lanza_error_y_no_persiste(
    plantilla_repo_mock,
):
    # Arrange
    plantilla_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = EliminarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaNoEncontradaError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaDiaCommand(plantilla_id=uuid4(), numero_dia=1)
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_dia_que_la_plantilla_no_tiene_propaga_el_error_del_dominio(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaDiaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaDiaCommand(plantilla_id=plantilla.id, numero_dia=8)
        )

    assert len(plantilla.dias) == 1
    plantilla_repo_mock.guardar.assert_not_awaited()
