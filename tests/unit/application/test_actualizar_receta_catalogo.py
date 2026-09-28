"""Pruebas del caso de uso `ActualizarRecetaCatalogoUseCase`."""

from decimal import Decimal
from uuid import uuid4

import pytest

from plan_nutricional.application.commands.commands import ActualizarRecetaCatalogoCommand
from plan_nutricional.application.use_cases.actualizar_receta_catalogo import (
    ActualizarRecetaCatalogoUseCase,
)
from plan_nutricional.domain.exceptions import RecetaCatalogoNoEncontradaError


def _comando(receta_id, nombre: str = "Avena integral") -> ActualizarRecetaCatalogoCommand:
    return ActualizarRecetaCatalogoCommand(
        receta_catalogo_id=receta_id,
        nombre=nombre,
        descripcion="Versión revisada",
        instrucciones="Cocer la avena en agua y añadir la fruta.",
        cantidad=Decimal("300"),
        unidad="g",
    )


async def test_actualizar_una_receta_existente_cambia_sus_datos_y_persiste(
    catalogo_repo_mock, receta_catalogo
):
    # Arrange
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = ActualizarRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act
    actualizada = await caso_de_uso.ejecutar(_comando(receta_catalogo.id))

    # Assert
    assert actualizada is receta_catalogo
    assert actualizada.nombre == "Avena integral"
    assert actualizada.porcion_default.cantidad == Decimal("300")
    catalogo_repo_mock.obtener_por_id.assert_awaited_once_with(receta_catalogo.id)
    catalogo_repo_mock.guardar.assert_awaited_once_with(receta_catalogo)


async def test_actualizar_una_receta_inexistente_lanza_error_y_no_persiste(
    catalogo_repo_mock,
):
    # Arrange
    catalogo_repo_mock.obtener_por_id.return_value = None
    caso_de_uso = ActualizarRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(RecetaCatalogoNoEncontradaError):
        await caso_de_uso.ejecutar(_comando(uuid4()))

    catalogo_repo_mock.guardar.assert_not_awaited()


async def test_actualizar_una_receta_dejando_el_nombre_vacio_no_persiste(
    catalogo_repo_mock, receta_catalogo
):
    # Arrange
    nombre_original = receta_catalogo.nombre
    catalogo_repo_mock.obtener_por_id.return_value = receta_catalogo
    caso_de_uso = ActualizarRecetaCatalogoUseCase(catalogo_repo_mock)

    # Act / Assert
    with pytest.raises(ValueError):
        await caso_de_uso.ejecutar(_comando(receta_catalogo.id, nombre=""))

    assert receta_catalogo.nombre == nombre_original
    catalogo_repo_mock.guardar.assert_not_awaited()
