"""Pruebas del caso de uso `EliminarPlantillaRecetaUseCase`."""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import EliminarPlantillaRecetaCommand
from plan_nutricional.application.use_cases.eliminar_plantilla_receta import (
    EliminarPlantillaRecetaUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlantillaNoEncontradaError,
    PlantillaRecetaNoEncontradaError,
    PlantillaTiempoComidaNoEncontradoError,
)
from plan_nutricional.domain.model import TipoTiempoComida


def _plantilla_con_receta(construir_plantilla):
    """Plantilla con día 1, DESAYUNO y una receta. Devuelve (plantilla, receta)."""
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    receta = plantilla.agregar_receta(
        numero_dia=1,
        tipo=TipoTiempoComida.DESAYUNO,
        receta_catalogo_id=uuid4(),
        cantidad=Decimal("200"),
        unidad="g",
    )
    return plantilla, receta


async def test_eliminar_una_receta_existente_de_la_plantilla_la_quita_y_persiste(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla, receta = _plantilla_con_receta(construir_plantilla)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaRecetaUseCase(plantilla_repo_mock)

    # Act
    await caso_de_uso.ejecutar(
        EliminarPlantillaRecetaCommand(
            plantilla_id=plantilla.id,
            numero_dia=1,
            tipo=TipoTiempoComida.DESAYUNO,
            receta_id=receta.id,
        )
    )

    # Assert
    assert plantilla.dias[0].tiempos_comida[0].recetas == []
    plantilla_repo_mock.obtener_por_id.assert_awaited_once_with(plantilla.id)
    plantilla_repo_mock.guardar.assert_awaited_once_with(plantilla)


async def test_eliminar_una_receta_de_una_plantilla_inexistente_no_persiste(
    plantilla_repo_mock,
):
    # Arrange
    plantilla_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = EliminarPlantillaRecetaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaNoEncontradaError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaRecetaCommand(
                plantilla_id=uuid4(),
                numero_dia=1,
                tipo=TipoTiempoComida.DESAYUNO,
                receta_id=uuid4(),
            )
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_una_receta_de_un_tiempo_de_comida_inexistente_propaga_el_error(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange — la receta está en DESAYUNO, se pide borrarla de CENA
    plantilla, receta = _plantilla_con_receta(construir_plantilla)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaRecetaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaTiempoComidaNoEncontradoError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaRecetaCommand(
                plantilla_id=plantilla.id,
                numero_dia=1,
                tipo=TipoTiempoComida.CENA,
                receta_id=receta.id,
            )
        )

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_eliminar_una_receta_que_no_existe_propaga_el_error_del_dominio(
    plantilla_repo_mock, construir_plantilla
):
    # Arrange
    plantilla, _ = _plantilla_con_receta(construir_plantilla)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    caso_de_uso = EliminarPlantillaRecetaUseCase(plantilla_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaRecetaNoEncontradaError):
        await caso_de_uso.ejecutar(
            EliminarPlantillaRecetaCommand(
                plantilla_id=plantilla.id,
                numero_dia=1,
                tipo=TipoTiempoComida.DESAYUNO,
                receta_id=uuid4(),
            )
        )

    assert len(plantilla.dias[0].tiempos_comida[0].recetas) == 1
    plantilla_repo_mock.guardar.assert_not_awaited()
