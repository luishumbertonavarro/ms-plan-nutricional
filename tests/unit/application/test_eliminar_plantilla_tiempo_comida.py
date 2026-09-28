"""Pruebas del caso de uso `EliminarPlantillaTiempoComidaUseCase`."""

from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import (
    EliminarPlantillaTiempoComidaCommand,
)
from plan_nutricional.application.use_cases.eliminar_plantilla_tiempo_comida import (
    EliminarPlantillaTiempoComidaUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlantillaDiaNoEncontradoError,
    PlantillaNoEncontradaError,
    PlantillaTiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model import TipoTiempoComida


async def test_eliminar_un_tiempo_de_comida_existente_de_la_plantilla_lo_quita_y_persiste(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.CENA)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaTiempoComidaUseCase(plantilla_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        EliminarPlantillaTiempoComidaCommand(
            plantilla_id=plantilla.id, numero_dia=1, tipo=TipoTiempoComida.DESAYUNO
        )
    )

    # Assert
    assert [t.tipo for t in plantilla.dias[0].tiempos_comida] == [TipoTiempoComida.CENA]
    plantilla_repo_mock.obtener_por_id.assert_awaited_once_with(plantilla.id)
    plantilla_repo_mock.guardar.assert_awaited_once_with(plantilla)


async def test_eliminar_un_tiempo_de_comida_de_una_plantilla_inexistente_no_persiste(
    plantilla_repo_mock,
):
    # Arrange
    plantilla_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = EliminarPlantillaTiempoComidaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaNoEncontradaError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaTiempoComidaCommand(
                plantilla_id=uuid4(), numero_dia=1, tipo=TipoTiempoComida.DESAYUNO
            )
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_tiempo_de_comida_de_un_dia_no_agregado_propaga_el_error(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaTiempoComidaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaDiaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaTiempoComidaCommand(
                plantilla_id=plantilla.id, numero_dia=4, tipo=TipoTiempoComida.DESAYUNO
            )
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_un_tiempo_de_comida_que_el_dia_no_tiene_propaga_el_error(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaTiempoComidaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaTiempoComidaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaTiempoComidaCommand(
                plantilla_id=plantilla.id, numero_dia=1, tipo=TipoTiempoComida.MERIENDA
            )
        )

    assert len(plantilla.dias[0].tiempos_comida) == 1
    plantilla_repo_mock.guardar.assert_not_awaited()
