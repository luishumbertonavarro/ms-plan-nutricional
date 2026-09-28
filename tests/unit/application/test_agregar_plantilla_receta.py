"""Pruebas del caso de uso `AgregarPlantillaRecetaUseCase`.

Es el único caso de uso de plantilla que trabaja con **dos** repositorios, así
que además de las ramas de error hay que verificar el **corto-circuito**: si la
plantilla no existe, el catálogo no debe consultarse siquiera.
"""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import AgregarPlantillaRecetaCommand
from plan_nutricional.application.use_cases.agregar_plantilla_receta import (
    AgregarPlantillaRecetaUseCase,
)
from plan_nutricional.domain.exceptions import (
    PlantillaDiaNoEncontradoError,
    PlantillaNoEncontradaError,
    PlantillaTiempoComidaNoEncontradoError,
    RecetaCatalogoInactivaError,
    RecetaCatalogoNoEncontradaError,
)
from plan_nutricional.domain.model import TipoTiempoComida


def _comando(plantilla_id, receta_catalogo_id, numero_dia: int = 1, tipo=None):
    return AgregarPlantillaRecetaCommand(
        plantilla_id=plantilla_id,
        numero_dia=numero_dia,
        tipo=tipo or TipoTiempoComida.DESAYUNO,
        receta_catalogo_id=receta_catalogo_id,
        cantidad=Decimal("200"),
        unidad="g",
    )


def _plantilla_lista(construir_plantilla):
    """Plantilla con el día 1 y su DESAYUNO ya creados."""
    plantilla = construir_plantilla()
    plantilla.agregar_dia(1)
    plantilla.agregar_tiempo_comida(1, TipoTiempoComida.DESAYUNO)
    return plantilla


async def test_agregar_una_receta_del_catalogo_a_la_plantilla_la_registra_y_persiste(
    plantilla_repo_mock, catalogo_repo_mock, construir_plantilla, receta_catalogo
):
    # Arrange
    plantilla = _plantilla_lista(construir_plantilla)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = AgregarPlantillaRecetaUseCase(plantilla_repo_mock, catalogo_repo_mock)

    # Act
    await caso_de_uso.ejecutar(_comando(plantilla.id, receta_catalogo.id))

    # Assert — se guarda la referencia al catálogo y la porción pedida
    recetas = plantilla.dias[0].tiempos_comida[0].recetas
    assert len(recetas) == 1
    assert recetas[0].receta_catalogo_id == receta_catalogo.id
    assert recetas[0].porcion.cantidad == Decimal("200")
    plantilla_repo_mock.guardar.assert_awaited_once_with(plantilla)


async def test_agregar_una_receta_a_una_plantilla_inexistente_ni_consulta_el_catalogo(
    plantilla_repo_mock, catalogo_repo_mock
):
    # Arrange — corto-circuito: debe abortar en la primera comprobación
    plantilla_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = AgregarPlantillaRecetaUseCase(plantilla_repo_mock, catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaNoEncontradaError):
        await caso_de_uso.ejecutar(_comando(uuid4(), uuid4()))

    catalogo_repo_mock.obtener_por_id.assert_not_awaited()
    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_agregar_una_receta_de_catalogo_inexistente_lanza_error_y_no_persiste(
    plantilla_repo_mock, catalogo_repo_mock, construir_plantilla
):
    # Arrange
    plantilla = _plantilla_lista(construir_plantilla)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = AgregarPlantillaRecetaUseCase(plantilla_repo_mock, catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(RecetaCatalogoNoEncontradaError):
        await caso_de_uso.ejecutar(_comando(plantilla.id, uuid4()))

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_agregar_una_receta_de_catalogo_inactiva_lanza_error_y_no_persiste(
    plantilla_repo_mock, catalogo_repo_mock, construir_plantilla, receta_catalogo
):
    # Arrange — una receta desactivada no puede incorporarse a una plantilla
    plantilla = _plantilla_lista(construir_plantilla)
    receta_catalogo.desactivar()
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = AgregarPlantillaRecetaUseCase(plantilla_repo_mock, catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(RecetaCatalogoInactivaError):
        await caso_de_uso.ejecutar(_comando(plantilla.id, receta_catalogo.id))

    assert plantilla.dias[0].tiempos_comida[0].recetas == []
    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_agregar_una_receta_a_un_dia_no_agregado_propaga_el_error_del_dominio(
    plantilla_repo_mock, catalogo_repo_mock, construir_plantilla, receta_catalogo
):
    # Arrange — la plantilla existe pero está vacía
    plantilla = construir_plantilla()
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = AgregarPlantillaRecetaUseCase(plantilla_repo_mock, catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaDiaNoEncontradoError):
        await caso_de_uso.ejecutar(_comando(plantilla.id, receta_catalogo.id))

    plantilla_repo_mock.guardar.assert_not_awaited()


async def test_agregar_una_receta_a_un_tiempo_de_comida_no_agregado_propaga_el_error(
    plantilla_repo_mock, catalogo_repo_mock, construir_plantilla, receta_catalogo
):
    # Arrange — el día 1 existe pero no tiene CENA
    plantilla = _plantilla_lista(construir_plantilla)
    plantilla_repo_mock.obtener_por_id.return_value = plantilla
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = AgregarPlantillaRecetaUseCase(plantilla_repo_mock, catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(PlantillaTiempoComidaNoEncontradoError):
        await caso_de_uso.ejecutar(
            _comando(plantilla.id, receta_catalogo.id, tipo=TipoTiempoComida.CENA)
        )

    plantilla_repo_mock.guardar.assert_not_awaited()
