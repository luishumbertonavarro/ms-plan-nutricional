"""Pruebas del caso de uso `AgregarPlantillaDiaUseCase`."""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import AgregarPlantillaDiaCommand
from plan_nutricional.application.use_cases.agregar_plantilla_dia import (
    AgregarPlantillaDiaUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlantillaDiaDuplicadoError,
    PlantillaDiaFueraDeDuracionError,
    PlantillaNoEncontradaError,
)


async def test_agregar_un_dia_valido_a_la_plantilla_lo_registra_y_persiste(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = AgregarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        AgregarPlantillaDiaCommand(plantilla_id=plantilla.id, numero_dia=3)
    )

    # Assert
    assert [d.numero_dia for d in plantilla.dias] == [3]
    plantilla_repo_mock.obtener_por_id.assert_awaited_once_with(plantilla.id)
    plantilla_repo_mock.guardar.assert_awaited_once_with(plantilla)


async def test_agregar_un_dia_a_una_plantilla_inexistente_lanza_error_y_no_persiste(
    plantilla_repo_mock,
):
    # Arrange
    plantilla_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = AgregarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaNoEncontradaError):
        await caso_de_uso.ejecutar(
            AgregarPlantillaDiaCommand(plantilla_id=uuid4(), numero_dia=1)
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_agregar_un_dia_fuera_de_la_duracion_de_la_plantilla_no_persiste(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange — la plantilla dura 15 días
    plantilla = construir_plantilla(dias_duracion=15)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = AgregarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaDiaFueraDeDuracionError):
        await caso_de_uso.ejecutar(
            AgregarPlantillaDiaCommand(plantilla_id=plantilla.id, numero_dia=16)
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_agregar_dos_veces_el_mismo_dia_a_la_plantilla_lanza_duplicado(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = AgregarPlantillaDiaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaDiaDuplicadoError):
        await caso_de_uso.ejecutar(
            AgregarPlantillaDiaCommand(plantilla_id=plantilla.id, numero_dia=1)
        )

    assert len(plantilla.dias) == 1
    plantilla_repo_mock.guardar.assert_not_awaited()
